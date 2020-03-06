import os
from beacon_shared.config import TIMINGS
from pulse_scheduler import PulseScheduler

if __name__ == '__main__':
    use_hsm = int(os.getenv('USE_HSM', 0)) == 1
    ctrl = PulseScheduler(**TIMINGS, use_hsm=use_hsm)
    ctrl.start()
