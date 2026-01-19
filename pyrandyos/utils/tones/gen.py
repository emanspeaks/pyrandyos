from struct import pack
from math import sin, pi


PACK_FMT = '<h'  # LE, signed 16-bit
BITRATE = 16
MAXVAL = 2**(BITRATE - 1) - 1


def generate_tone(freq_hz: float = 440,
                  dur_s: float = 0.5,
                  sample_rate_hz: int = 48000,
                  volume: float = 0.5,
                  fade_dur_s: float = .005):
    """
    Generate a sine wave tone with fade in/out to prevent pops.
    """
    total = int(sample_rate_hz*dur_s)
    fade = int(sample_rate_hz*fade_dur_s)
    # tail = total - fade
    ampl = MAXVAL*volume
    twopifreq_smplrt = 2*pi*freq_hz/sample_rate_hz

    return b''.join(pack(PACK_FMT,
                         int(ampl
                             * min(i/fade, 1)
                             * min((total - i)/fade, 1)
                             * sin(twopifreq_smplrt*i)))
                    for i in range(total))
