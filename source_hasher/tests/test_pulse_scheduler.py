import unittest
from datetime import timedelta
from pulse_scheduler import PulseScheduler

class TestPulseScheduler(unittest.TestCase):

    def test_args(self):
        self.assertRaises(ValueError, lambda: PulseScheduler(
            3, 4, 4, 4, 4
        ))

    def test_valid_timings(self):
        # from Table 13
        valid_timings = [
            [60, 0.2, 0.1, 0.1, 0.1],
            [60, 2, 1, 1, 1],
            [60, 0, 1, 1, 1],
            [60, 1, 1, 1, 1],
            [60, 5, 3, 3, 1],
            [60, 30, 8, 2, 2],
            [60, 59, 0.5, 0.5, 0.5]
        ]
        slack_accuracy = [
            [0.1, 0.1, 0.2],
            [1, 1, 2],
            [1, 1, 2],
            [2, 1, 2],
            [2, 3, 4],
            [15, 13, 13], # NOTE value in publication is wrong here
            [5, 53.5, 53.5]
        ]

        for i, timing in enumerate(valid_timings):
            args = [timedelta(seconds=x) for x in timing]
            s = PulseScheduler(*args)
            a = [timedelta(seconds=x) for x in slack_accuracy[i]]
            self.assertEqual(s.get_tuning_slack(a[0]), a[1], "Tuning slack wrong for entry {}".format(i))
            self.assertEqual(s.get_time_accuracy(a[0]), a[2], "Time accuracy wrong for entry {}".format(i))

    def test_invalid_timings(self):
        # from Table 14
        invalid_timings = [
            [60, 5, 1, 2, 1],
            [60, 11, 5, 8, 5],
            [60, 10, 14, 3, 3],
            [60, 55, 10, 8, 2],
            [60, 57, 12, 3, 3]
        ]

        for i, timing in enumerate(invalid_timings):
            args = [timedelta(seconds=x) for x in timing]
            self.assertRaises(ValueError, lambda: PulseScheduler(*args))


if __name__ == '__main__':
    unittest.main()
