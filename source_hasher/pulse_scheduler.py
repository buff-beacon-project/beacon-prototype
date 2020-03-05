import time
from sched import scheduler
from datetime import timedelta, datetime
from randomness_sources import RandomnessSources
from beacon_shared.hashing import hash_many
from beacon_shared.pulse import assemble_pulse
from exceptions import LatePulseException
from signer import Signer

class PulseScheduler:
    """
    Object to schedule pulse calculation and emmission times

    Arguments
    ---------
    period - The ideal period of pulses (corresponds to $\pi$)
    anticipation - The time before pulse timestamp to start assembling the pulse (corresponds to $\Delta$)
    max_delay - The maximum allowed delay for emission after the pulse timestamp (corresponds to $\delta$)
    max_local_skew_ahead - The max allowed local clock skew ahead of UTC (corresponds to $\sigma^+$)
    max_local_skew_behind - The max allowed local clock skew behind UTC (corresponds to $\sigma^-$)
    """
    def __init__(self, period, anticipation, max_delay, max_local_skew_behind, max_local_skew_ahead, use_hsm = True):

        for arg in [period, anticipation, max_delay, max_local_skew_ahead, max_local_skew_behind]:
            if not isinstance(arg, timedelta):
                raise ValueError("Provided argument is not a timedelta")

        # validate provided timings
        # as per Appendix A.1
        # -------------------------

        # R1
        if max_local_skew_ahead >= period / 10 or max_local_skew_behind >= period / 10:
            raise ValueError("The maximum clock skew provided is too large for the period")

        # R2
        if max_delay < max_local_skew_behind:
            raise ValueError("The maximum delay provided is too large for provided clock skew")

        # R3 (partial)
        if max_delay >= period / 4 - max_local_skew_ahead:
            raise ValueError("The maximum delay provided is too large and would result in a late pulse")

        # R4
        if anticipation >= period - max_local_skew_ahead:
            raise ValueError("The anticipation value provided is too large for the other provided timings")

        self.period = period
        self.anticipation = anticipation
        self.max_delay = max_delay
        self.max_local_skew_ahead = max_local_skew_ahead
        self.max_local_skew_behind = max_local_skew_behind

        self.now = time.perf_counter
        self.randomness_sources = RandomnessSources()
        self.signer = Signer(use_hsm)

    @property
    def max_pulse_generation_time(self):
        """
        corresponds to $\gamma$
        """
        return self.max_delay + self.anticipation - self.max_local_skew_ahead

    def get_tuning_slack(self, pulse_generation_time):
        """
        calculation of tuning slack $\eta$ based on Appendix A.1
        """
        pulse_generation_time = self.max_pulse_generation_time if pulse_generation_time == None else pulse_generation_time
        # R5
        eta = max(self.max_local_skew_ahead, self.max_local_skew_behind)
        # R6
        eta = max(eta, self.max_delay - self.max_local_skew_behind)
        # R7
        eta = max(eta, self.anticipation - pulse_generation_time - self.max_local_skew_ahead)

        return eta

    def get_time_accuracy(self, pulse_generation_time):
        """
        calculation of time accuracy $\alpha$ based on Appendix A.1
        """
        pulse_generation_time = self.max_pulse_generation_time if pulse_generation_time == None else pulse_generation_time
        delta_prime = max(self.max_delay, pulse_generation_time - self.anticipation)
        return max(
            self.anticipation - pulse_generation_time - self.max_local_skew_behind,
            delta_prime + self.max_local_skew_ahead
        )

    def get_local_random_value(self):
        values = self.randomness_sources.fetch()
        return hash_many(values)

    def recall_state(self):
        # TODO implement memory
        self.chain_index = 0
        self.previous_pulse = None
        self.local_random_value = None

    def generate_pulse(self, next_local_random_value):
        self.current_pulse = assemble_pulse(
            signer = self.signer,
            chain_index = self.chain_index,
            local_random_value = self.local_random_value,
            next_local_random_value = next_local_random_value,
            previous_pulse = self.previous_pulse
        )

    def emit_pulse(self):
        pulse = self.current_pulse
        self.previous_pulse = self.current_pulse
        self.current_pulse = None

    def get_next_pulse_generation_delay(self):
        if self.previous_pulse == None:
            return timedelta(seconds=0)

        next_pulse_time = self.previous_pulse["timeStamp"].get() + self.period
        return next_pulse_time - self.anticipation

    def start(self):
        self.chain_index = 0
        self.previous_pulse = None
        self.current_pulse = None
        self.local_random_value = None
        self.recall_state()

        def callback():
            started_at = self.now()
            next_local_random_value = self.get_local_random_value()
            self.generate_pulse()
            generation_time = self.now() - started_at
            if generation_time > self.max_pulse_generation_time:
                raise LatePulseException()
            self.emit_pulse()
            self.local_random_value = next_local_random_value

        s = scheduler(self.now, time.sleep)

        while True:
            try:
                delay = self.get_next_pulse_generation_delay().total_seconds()
                if delay < 0:
                    raise LatePulseException()
                s.enter(delay, callback)
                s.run(blocking = True)

            # TODO handle exceptions
            except Exception as e:
                print(e)
