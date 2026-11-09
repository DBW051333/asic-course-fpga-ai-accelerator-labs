"""AX7020 single-bank shared256 Lab8 driver. No buffer allocation or feature reads inside inference timing."""
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
        if real_board:
            from ax7020_runtime import buffer_report
            self.buffer_evidence = {'tx': buffer_report(self.tx), 'rx': buffer_report(self.rx)}
        self.regs.write(4, 1)
        self._closed = False

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

    def _exchange(self, send_bytes, receive_capacity):
        self.rx.fill(0)
        # Include arming the receive channel and starting the send channel.
        started = time.perf_counter_ns()
        try:
            self.dma.recvchannel.transfer(self.rx, nbytes=receive_capacity)
            self.dma.sendchannel.transfer(self.tx, nbytes=send_bytes)
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
        x = np.asarray(sample)
        if x.shape != (512,) or not np.issubdtype(x.dtype, np.integer):
            raise ValueError('sample must contain exactly 512 signed integer values')
        if np.any(x < -128) or np.any(x > 127):
            raise ValueError('sample values must lie in [-128,127]')
        self.tx[:8] = np.frombuffer((1).to_bytes(8, 'little'), dtype=np.uint8)
        self.tx[8:] = x.astype(np.int8).view(np.uint8)
        count, elapsed_ns = self._exchange(520, 8)
        if count != 1 or int(self.rx[0]) not in (0, 1):
            raise RuntimeError(f'Invalid classification response: bytes={count}, code={int(self.rx[0]):02x}')
        compute = self.regs.read(0x18)
        transaction = self.regs.read(0x1C)
        if self.regs.read(0x20) != 520 or self.regs.read(0x24) != 1:
            raise RuntimeError('Hardware packet byte counters disagree with the inference protocol')
        return {'prediction': int(self.rx[0]), 'compute_cycles': compute,
                'compute_us': compute * 1e6 / self.clock_hz,
                'pl_transaction_cycles': transaction,
                'pl_transaction_us': transaction * 1e6 / self.clock_hz,
                'ps_end_to_end_us': elapsed_ns / 1000}

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
        if not (self.dma.sendchannel.idle and self.dma.recvchannel.idle):
            self.reset_dma()  # Ensure buffers are no longer targeted by DMA.
        self.tx.freebuffer()
        self.rx.freebuffer()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
