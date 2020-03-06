import traceback
import time
import signal
from sched import scheduler
from datetime import timedelta, datetime
from randomness_sources import RandomnessSources
from beacon_shared.types import ByteHash
from beacon_shared.hashing import hash_many
from beacon_shared.pulse import assemble_pulse, set_pulse_status, pulse_to_json
from beacon_shared.store import BeaconStore
from exceptions import BeaconException, LatePulseException
from signer import Signer

class ProgramKilled(Exception):
    pass

def clear_schedule_queue(s):
    for e in s.queue:
        s.cancel(e)

class PulseScheduler:
    """
    Object to schedule pulse calculation and emmission times

    Arguments
    ---------
    period - The ideal period of pulses (corresponds to $\pi$)
    anticipation - The time before pulse timestamp to start assembling the pulse (corresponds to $\Delta$)
    delay - The delay for emission after the pulse timestamp (corresponds to $\delta$)
    max_local_skew_ahead - The max allowed local clock skew ahead of UTC (corresponds to $\sigma^+$)
    max_local_skew_behind - The max allowed local clock skew behind UTC (corresponds to $\sigma^-$)
    """
    def __init__(self, period, anticipation, delay, max_local_skew_behind, max_local_skew_ahead, use_hsm = True):

        for arg in [period, anticipation, delay, max_local_skew_ahead, max_local_skew_behind]:
            if not isinstance(arg, timedelta):
                raise ValueError("Provided argument is not a timedelta")

        # validate provided timings
        # as per Appendix A.1
        # -------------------------

        # R1
        if max_local_skew_ahead >= period / 10 or max_local_skew_behind >= period / 10:
            raise ValueError("The maximum clock skew provided is too large for the period")

        # R2
        if delay < max_local_skew_behind:
            raise ValueError("The maximum delay provided is too large for provided clock skew")

        # R3 (partial)
        if delay >= period / 4 - max_local_skew_ahead:
            raise ValueError("The maximum delay provided is too large and would result in a late pulse")

        # R4
        if anticipation >= period - max_local_skew_ahead:
            raise ValueError("The anticipation value provided is too large for the other provided timings")

        self.period = period
        self.anticipation = anticipation
        self.delay = delay
        self.max_local_skew_ahead = max_local_skew_ahead
        self.max_local_skew_behind = max_local_skew_behind

        self.randomness_sources = RandomnessSources()
        self.signer = Signer(use_hsm)

        self.store = BeaconStore()
        self.store.initDB()
        # TODO: this should be changed
        self.store.addCertificate(
            self.signer.get_certificate_id().hex(),
            self.signer.get_certificate().hex()
        )

    def now(self):
        return datetime.now()

    @property
    def max_pulse_generation_time(self):
        """
        corresponds to $\gamma$
        """
        return self.delay + self.anticipation - self.max_local_skew_ahead

    def get_tuning_slack(self, pulse_generation_time = None):
        """
        calculation of tuning slack $\eta$ based on Appendix A.1
        """
        pulse_generation_time = self.max_pulse_generation_time if pulse_generation_time == None else pulse_generation_time
        # R5
        eta = max(self.max_local_skew_ahead, self.max_local_skew_behind)
        # R6
        eta = max(eta, self.delay - self.max_local_skew_behind)
        # R7
        eta = max(eta, self.anticipation - pulse_generation_time - self.max_local_skew_ahead)

        return eta

    def get_time_accuracy(self, pulse_generation_time = None):
        """
        calculation of time accuracy $\alpha$ based on Appendix A.1
        """
        pulse_generation_time = self.max_pulse_generation_time if pulse_generation_time == None else pulse_generation_time
        delta_prime = max(self.delay, pulse_generation_time - self.anticipation)
        return max(
            self.anticipation - pulse_generation_time - self.max_local_skew_behind,
            delta_prime + self.max_local_skew_ahead
        )

    def get_local_random_value(self):
        values = self.randomness_sources.fetch()
        return ByteHash(hash_many(values))

    def recall_state(self):
        self.chain_index = 0
        self.previous_pulse = None
        self.local_random_value = None

        self.previous_pulse = self.store.fetchLatestPulse()

        print('last pulse', pulse_to_json(self.previous_pulse, sort_keys=True, indent=4))

        if self.previous_pulse == None:
            return

        self.chain_index = self.previous_pulse["chainIndex"].get()

        if self.local_random_value == None:
            # TODO: need better handling of picking up where we left off
            self.local_random_value = self.get_local_random_value()
            self.chain_index += 1
            self.previous_pulse = None
            print('new chain')

    def generate_pulse(self, next_local_random_value):
        self.current_pulse = assemble_pulse(
            signer = self.signer,
            chain_index = self.chain_index,
            local_random_value = self.local_random_value,
            next_local_random_value = next_local_random_value,
            previous_pulse = self.previous_pulse
        )
        # first pulse... so modify the timestamp to give enough time to calculate
        if self.current_pulse['pulseIndex'].get() == 0:
            self.current_pulse['timeStamp'].set(self.current_pulse['timeStamp'].get() + self.anticipation)

    def emit_pulse(self):
        self.store.addPulse(self.current_pulse)
        print("Releasing pulse", pulse_to_json(self.current_pulse, sort_keys=True, indent=4))
        self.previous_pulse = self.current_pulse
        self.current_pulse = None

    def get_next_pulse_generation_delay(self):
        if self.previous_pulse == None:
            return timedelta(seconds=0)

        next_pulse_time = self.previous_pulse["timeStamp"].get() + self.period
        return next_pulse_time - self.anticipation - self.now()

    def get_pulse_release_delay(self, pulse):
        return pulse["timeStamp"].get() + self.delay - self.now()

    def start(self):
        self.chain_index = 0
        self.previous_pulse = None
        self.current_pulse = None
        self.local_random_value = None
        self.recall_state()

        self.next_local_random_value = None

        def generate():
            self.pulse_generation_started_at = self.now()
            started_at = time.perf_counter()
            self.next_local_random_value = self.get_local_random_value()
            self.generate_pulse(self.next_local_random_value)
            self.pulse_generation_duration = timedelta(seconds=(time.perf_counter() - started_at))

        def release():
            self.emit_pulse()
            self.local_random_value = self.next_local_random_value

        def exit_handler():
            raise ProgramKilled

        signal.signal(signal.SIGTERM, exit_handler)
        signal.signal(signal.SIGINT, exit_handler)

        # time.time is the system clock. Normally this is not preferred for
        # use with calculating time deltas, but in this case I think it's the
        # best choice so that when the system syncs with a time server
        # the events are scheduled based on that update
        s = scheduler(time.time, time.sleep)

        while True:
            try:
                print('Generating next pulse of chain {}'.format(self.chain_index), flush=True)
                # Wait then generate the next pulse
                wait_for = self.get_next_pulse_generation_delay().total_seconds()
                s.enter(wait_for, 0, generate)
                s.run(blocking = True)

                # wait then release the generated pulse
                pulse = self.current_pulse
                wait_for = self.get_pulse_release_delay(pulse).total_seconds()
                if wait_for < 0:
                    set_pulse_status(pulse, STATUS_GAP)
                    release()
                    print('Warning: pulse {} was late'.format(pulse["pulseIndex"].get()), flush=True)
                else:
                    s.enter(wait_for, 0, release)
                    s.run(blocking = True)

                # record the status
                idealCalculationTime = pulse['timeStamp'].get() - self.anticipation
                calculationStartDelay = self.pulse_generation_started_at - idealCalculationTime
                eta = self.get_tuning_slack(self.pulse_generation_duration)
                etaMax = self.get_tuning_slack()
                alpha = self.get_time_accuracy(self.pulse_generation_duration)
                alphaMax = self.get_time_accuracy()
                print("STATUS\n--------")
                print("calculation started at: {} (dt from ideal: {}s)".format(
                    self.pulse_generation_started_at,
                    calculationStartDelay.total_seconds()
                ))
                print("generation duration: {}s\ntuning slack: {}s ({}s maximum)\ntime accuracy: {}s ({}s maximum)".format(
                    self.pulse_generation_duration.total_seconds(),
                    eta.total_seconds(),
                    etaMax.total_seconds(),
                    alpha.total_seconds(),
                    alphaMax.total_seconds()
                ), flush=True)

            # TODO handle exceptions
            except BeaconException as e:
                print('ERROR:', e)
                traceback.print_exc()

            except ProgramKilled as e:
                clear_schedule_queue(s)
                exit(0)

            except Exception as e:
                print('UNRECOVERABLE ERROR:', e)
                traceback.print_exc()
                clear_schedule_queue(s)
                exit(1)
