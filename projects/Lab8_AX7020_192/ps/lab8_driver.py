"""AX7020 Lab8 driver. Separate API time and host DMA-call window; allocation policy is preserved."""
from pathlib import Path
import time
import numpy as np

class Lab8NPU:
    def __init__(self, bitfile=None, timeout=2.0, overlay=None, allocator=None):
        real_board = overlay is None
        self.clock_evidence = None
        if overlay is None:
            from pynq import Overlay, allocate
            bitfile = Path(bitfile or Path(__file__).parent / 'lab8.bit')
            overlay = Overlay(str(bitfile))
            allocator = allocate
        self.overlay = overlay
        self.dma = overlay.axi_dma_0
        self.regs = overlay.npu_0.mmio
        self.timeout = timeout
        if self.regs.read(0) != 0x4C414238:
            raise RuntimeError('Lab8 register signature mismatch; check bit/hwh pairing')
        self.clock_hz = self.regs.read(0x0C)
        if self.clock_hz != 142_857_132:
            raise RuntimeError('This baseline requires a 142.857132 MHz PL clock')
        if real_board:
            from ax7020_runtime import clock_report
            self.clock_evidence = clock_report(self.regs)
            self.clock_hz = self.clock_evidence['register_derived_hz']
        self.tx = allocator(shape=(520,), dtype=np.uint8)
        self.rx = allocator(shape=(168,), dtype=np.uint8)
        self.regs.write(4, 1)
        self._closed = False
        self._allocator = allocator
        self.batch_tx = self.batch_rx = None
        self.batch_capacity = 0
        self._real_board = real_board
        if real_board:
            from ax7020_runtime import buffer_report
            self.buffer_evidence = {'tx': buffer_report(self.tx), 'rx': buffer_report(self.rx)}

    def _wait_dma(self):
        deadline = time.perf_counter() + self.timeout
        while True:
            for channel in (self.dma.sendchannel, self.dma.recvchannel):
                if channel.error:
                    raise RuntimeError('DMA error: ' + str(self.dma.register_map))
            if self.dma.sendchannel.idle and self.dma.recvchannel.idle:
                break
            if time.perf_counter() >= deadline:
                raise TimeoutError('DMA timeout: ' + str(self.dma.register_map))
        # PYNQ wait() performs receive cache invalidation and records the
        # actual received byte count. Both channels are already idle.
        self.dma.sendchannel.wait()
        self.dma.recvchannel.wait()

    def _exchange(self, send_bytes, receive_capacity, tx=None, rx=None):
        tx = self.tx if tx is None else tx
        rx = self.rx if rx is None else rx
        clear_started = time.perf_counter_ns()
        rx.fill(0)
        self._last_rx_clear_ns = time.perf_counter_ns() - clear_started
        # Include arming the receive channel and starting the send channel.
        started = time.perf_counter_ns()
        try:
            self.dma.recvchannel.transfer(rx, nbytes=receive_capacity)
            self.dma.sendchannel.transfer(tx, nbytes=send_bytes)
            self._wait_dma()
        except Exception:
            self.reset_dma()
            raise
        elapsed_ns = time.perf_counter_ns() - started
        return int(self.dma.recvchannel.transferred), elapsed_ns

    def reset_dma(self):
        """Bounded DMA and NPU reset after a failed transaction."""
        self.regs.write(4, 1)
        self.dma.mmio.write(0, 4)  # Resetting either channel resets the whole DMA.
        deadline = time.perf_counter() + self.timeout
        while self.dma.mmio.read(0) & 4:
            if time.perf_counter() >= deadline:
                raise TimeoutError('DMA reset did not finish; reload the overlay')
        # Verify channel run-state before calling PYNQ's unbounded start().
        for offset in (0, 0x30):
            self.dma.mmio.write(offset, 1)
        while not (self.dma.sendchannel.running and self.dma.recvchannel.running):
            if time.perf_counter() >= deadline:
                raise TimeoutError('DMA restart did not finish; reload the overlay')
        self.dma.sendchannel.start()
        self.dma.recvchannel.start()

    def infer(self, sample):
        api_started = time.perf_counter_ns()
        x = np.asarray(sample)
        if x.shape != (512,) or not np.issubdtype(x.dtype, np.integer):
            raise ValueError('sample must contain exactly 512 signed integer values')
        if np.any(x < -128) or np.any(x > 127):
            raise ValueError('sample values must lie in [-128,127]')
        self.tx[:8] = np.frombuffer((1).to_bytes(8, 'little'), dtype=np.uint8)
        self.tx[8:] = x.astype(np.int8).view(np.uint8)
        packed_at = time.perf_counter_ns()
        count, elapsed_ns = self._exchange(520, 8)
        exchanged_at = time.perf_counter_ns()
        if count != 1 or int(self.rx[0]) not in (0, 1):
            raise RuntimeError(f'Invalid classification response: bytes={count}, code={int(self.rx[0]):02x}')
        compute = self.regs.read(0x18)
        transaction = self.regs.read(0x1C)
        if self.regs.read(0x20) != 520 or self.regs.read(0x24) != 1:
            raise RuntimeError('Hardware packet byte counters disagree with the inference protocol')
        result = {'prediction': int(self.rx[0]), 'compute_cycles': compute,
                'compute_us': compute * 1e6 / self.clock_hz,
                'pl_transaction_cycles': transaction,
                'pl_transaction_us': transaction * 1e6 / self.clock_hz,
                'ps_end_to_end_us': elapsed_ns / 1000}
        return self._timing_result(result, api_started, packed_at, exchanged_at, elapsed_ns)

    def _dma_available(self):
        # PYNQ 3.0.1 starts a fresh simple-DMA channel with Idle=0 until
        # its first completed transfer. The library explicitly permits this
        # state via _first_transfer; active transfers still cannot resize.
        return all(c.idle or (getattr(c, '_first_transfer', False)
                             and c.running and not c.error)
                   for c in (self.dma.sendchannel, self.dma.recvchannel))

    def prepare_batch(self, capacity=42):
        """Allocate reusable buffers before inference timing; max DMA length is 23 bits."""
        if not isinstance(capacity, (int, np.integer)) or not 1 <= capacity <= 16383:
            raise ValueError('batch capacity must be an integer in [1,16383]')
        if capacity <= self.batch_capacity:
            return
        if not self._dma_available():
            raise RuntimeError('Cannot resize buffers while DMA is running')
        tx = self._allocator(shape=(8 + capacity * 512,), dtype=np.uint8)
        try:
            rx = self._allocator(shape=(capacity * 8,), dtype=np.uint8)
        except Exception:
            tx.freebuffer()
            raise
        if self.batch_tx is not None:
            self.batch_tx.freebuffer()
            self.batch_rx.freebuffer()
        self.batch_tx, self.batch_rx, self.batch_capacity = tx, rx, capacity
        if self._real_board:
            from ax7020_runtime import buffer_report
            self.buffer_evidence.update(batch_tx=buffer_report(tx), batch_rx=buffer_report(rx))

    def infer_batch(self, samples):
        """CMD3 with total API timing (including allocation if needed)."""
        api_started = time.perf_counter_ns()
        x = np.asarray(samples)
        if x.ndim != 2 or x.shape[1] != 512 or not np.issubdtype(x.dtype, np.integer):
            raise ValueError('samples must have integer shape (N,512)')
        count = x.shape[0]
        if not 1 <= count <= 16383 or np.any(x < -128) or np.any(x > 127):
            raise ValueError('invalid batch size or signed int8 input range')
        self.prepare_batch(count)
        header = (count << 32) | 3
        self.batch_tx[:8] = np.frombuffer(header.to_bytes(8, 'little'), dtype=np.uint8)
        self.batch_tx[8:8 + count * 512] = x.astype(np.int8).view(np.uint8).reshape(-1)
        packed_at = time.perf_counter_ns()
        received, elapsed_ns = self._exchange(8 + count * 512, count * 8, self.batch_tx, self.batch_rx)
        exchanged_at = time.perf_counter_ns()
        data = np.array(self.batch_rx[:count * 8]).reshape(count, 8)
        if received != count * 8 or np.any(data[:, 0] > 1) or np.any(data[:, 3:] != 0):
            raise RuntimeError(f'Invalid batch response: bytes={received}')
        scores = data[:, 1:3].copy().view(np.int8)
        if np.any(data[:, 0] != (scores[:, 0] < scores[:, 1])):
            raise RuntimeError('Batch classes disagree with signed scores')
        if self.regs.read(0x20) != 8 + count * 512 or self.regs.read(0x24) != count * 8:
            raise RuntimeError('Hardware byte counters disagree with batch protocol')
        transaction = self.regs.read(0x1C)
        compute = self.regs.read(0x18)
        result = {'predictions': data[:, 0].copy(), 'scores': scores,
                'compute_cycles': compute, 'compute_us': compute * 1e6 / self.clock_hz,
                'pl_transaction_cycles': transaction,
                'pl_transaction_us': transaction * 1e6 / self.clock_hz,
                'ps_end_to_end_us': elapsed_ns / 1000,
                'samples_per_second': count * 1e9 / elapsed_ns}
        return self._timing_result(result, api_started, packed_at, exchanged_at, elapsed_ns)

    def _timing_result(self, result, api_started, packed_at, exchanged_at, elapsed_ns):
        # Compatibility name ps_end_to_end_us retains the historic DMA window.
        # PL and PS windows have different boundaries and must not be subtracted.
        result.update(host_dma_window_us=elapsed_ns / 1000,
                      validation_allocation_pack_us=(packed_at-api_started) / 1000,
                      receive_clear_us=self._last_rx_clear_ns / 1000,
                      parse_statistics_us=(time.perf_counter_ns()-exchanged_at) / 1000)
        result['api_inside_us'] = (time.perf_counter_ns()-api_started) / 1000
        return result

    def features(self):
        self.tx[:8] = np.frombuffer((2).to_bytes(8, 'little'), dtype=np.uint8)
        count, elapsed_ns = self._exchange(8, 168)
        if count != 162:
            raise RuntimeError(f'Invalid feature response: bytes={count}, code={int(self.rx[0]):02x}')
        if self.regs.read(0x20) != 8 or self.regs.read(0x24) != 162:
            raise RuntimeError('Hardware feature byte counters disagree with the protocol')
        data = np.array(self.rx[:162], dtype=np.uint8).view(np.int8)
        return {'fc1': data[:128], 'fc2': data[128:160], 'fc3': data[160:],
                'ps_readback_us': elapsed_ns / 1000}

    def close(self):
        if self._closed:
            return
        if not self._dma_available():
            self.reset_dma()  # Ensure buffers are no longer targeted by DMA.
        if self.batch_tx is not None:
            self.batch_tx.freebuffer()
            self.batch_rx.freebuffer()
        self.tx.freebuffer()
        self.rx.freebuffer()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
