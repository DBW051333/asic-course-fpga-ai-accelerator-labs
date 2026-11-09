"""Read-only AX7020 clock and DMA-buffer reachability checks."""
import time

PS_REFERENCE_HZ = 33_333_333.0
TARGET_HZ = 166_666_672
DDR_LIMIT = 0x40000000

def clock_report(regs=None, target_hz=TARGET_HZ):
    from pynq import MMIO, Clocks
    slcr = MMIO(0xF8000000, 0x200)
    values = {offset: slcr.read(offset) for offset in (0x100, 0x104, 0x108, 0x10C, 0x170)}
    ctrl = values[0x170]
    source = (ctrl >> 4) & 3
    pll_offset = (0x108, 0x108, 0x100, 0x104)[source]
    pll = values[pll_offset]
    feedback = (pll >> 12) & 127
    div0, div1 = (ctrl >> 8) & 63, (ctrl >> 20) & 63
    lock_bit = {0x100: 0, 0x104: 1, 0x108: 2}[pll_offset]
    if not div0 or not div1 or pll & 0x19 or not values[0x10C] & (1 << lock_bit):
        raise RuntimeError('PLL bypass/reset/unlocked or invalid FCLK divisors: ' + str(values))
    hz = PS_REFERENCE_HZ * feedback / (div0 * div1)
    if abs(hz / target_hz - 1) > 0.001:
        raise RuntimeError(f'Actual AX7020 FCLK0 {hz} Hz differs from target; do not change PLL blindly')
    report = {'raw_slcr': {hex(k): hex(v) for k, v in values.items()},
              'ps_reference_hz': PS_REFERENCE_HZ, 'pll_source_offset': hex(pll_offset),
              'pll_feedback': feedback, 'divisor0': div0, 'divisor1': div1,
              'register_derived_hz': hz, 'pynq_reported_mhz_assuming_50mhz': float(Clocks.fclk0_mhz),
              'scope': 'Register-derived clock with specified board crystal; tick estimates use host monotonic time; no instrument measurement'}
    if regs is not None:
        estimates = []
        for delay in (0.1, 0.2, 0.4):
            t0 = time.perf_counter(); v0 = regs.read(0x30)
            time.sleep(delay)
            v1 = regs.read(0x30); t1 = time.perf_counter()
            estimates.append(((v1 - v0) & 0xFFFFFFFF) / (t1 - t0))
        report['tick_estimates_hz'] = estimates
        if any(abs(v / hz - 1) > 0.02 for v in estimates):
            raise RuntimeError('NPU tick clock disagrees with PLL/FCLK register calculation')
    return report

def buffer_report(buffer):
    address, size = int(buffer.physical_address), int(buffer.nbytes)
    if address < 0 or size <= 0 or address + size > DDR_LIMIT:
        raise RuntimeError(f'DMA buffer outside AX7020 DDR map: {address:#x}+{size}')
    return {'physical_address': hex(address), 'nbytes': size, 'end_exclusive': hex(address + size)}
