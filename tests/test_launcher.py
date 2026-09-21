"""The start screen: picking a source, a participant and a matrix with the mouse."""
import unittest

from pyspeller.config import SpellerConfig

try:
    import tkinter
    tkinter.Tk().destroy()
    HAVE_DISPLAY = True
except Exception:                     # pragma: no cover - depends on the machine
    HAVE_DISPLAY = False


@unittest.skipUnless(HAVE_DISPLAY, 'no tk display available')
class TestSessionLauncher(unittest.TestCase):
    def setUp(self):
        from pyspeller.gui.launcher import SessionLauncher
        self.launcher = SessionLauncher(SpellerConfig())
        self.addCleanup(self.launcher.root.destroy)

    def test_the_simulator_is_offered_without_any_hardware(self):
        self.assertEqual(self.launcher.source.get(), 'simulator')
        choices = self.launcher.start()
        self.assertEqual(choices['source'], 'simulator')
        self.assertIsNone(choices['lsl_name'])

    def test_the_chosen_settings_come_back(self):
        self.launcher.subject.set('S07')
        self.launcher.experiment.set('p300')
        self.launcher.layout.set('3x3')
        self.launcher.repetitions.set(8)
        self.launcher.record.set(False)
        choices = self.launcher.start()
        self.assertEqual(choices['subject'], 'S07')
        self.assertEqual(choices['experiment'], 'p300')
        self.assertEqual(choices['layout'], '3x3')
        self.assertEqual(choices['n_repetitions'], 8)
        self.assertFalse(choices['record'])

    def test_blank_names_fall_back_to_defaults(self):
        self.launcher.subject.set('   ')
        self.launcher.experiment.set('')
        choices = self.launcher.start()
        self.assertEqual((choices['subject'], choices['experiment']),
                         ('test', 'speller'))

    def test_choosing_an_amplifier_without_scanning_is_refused(self):
        self.launcher.source.set('lsl')
        self.assertIsNone(self.launcher.start())
        self.assertIsNone(self.launcher.choices)
        self.assertIn('scan', self.launcher.status.get())

    def test_a_scanned_amplifier_can_be_picked(self):
        self.launcher.source.set('lsl')
        self.launcher._show_streams([
            {'name': 'g.USBamp-UB-2016', 'type': 'EEG', 'channels': 16,
             'fsample': 256.0},
            {'name': 'markers', 'type': 'Markers', 'channels': 1, 'fsample': 0.0},
        ])
        self.assertEqual(len(self.launcher.streams), 1)   # no irregular streams
        self.assertEqual(self.launcher.stream_list.size(), 1)
        self.assertIn('g.USBamp', self.launcher.stream_list.get(0))
        self.assertIn('256', self.launcher.stream_list.get(0))
        choices = self.launcher.start()
        self.assertEqual(choices['source'], 'lsl')
        self.assertEqual(choices['lsl_name'], 'g.USBamp-UB-2016')
        self.assertEqual(choices['lsl_type'], 'EEG')

    def test_cancelling_returns_nothing(self):
        self.launcher.cancel()
        self.assertIsNone(self.launcher.choices)


@unittest.skipUnless(HAVE_DISPLAY, 'no tk display available')
class TestChoicesReachTheSession(unittest.TestCase):
    """What the launcher returns must configure the run the same way flags do."""

    def test_choices_are_folded_into_the_arguments_and_config(self):
        import argparse
        from pyspeller.cli import _apply_choices
        config = SpellerConfig()
        args = argparse.Namespace(lsl=False, lsl_name=None, lsl_type='EEG',
                                  save=False, subject='test', experiment='speller')
        _apply_choices(args, config, {'source': 'lsl', 'lsl_name': 'g.Nautilus',
                                      'lsl_type': 'EEG', 'layout': '3x3',
                                      'n_repetitions': 5, 'record': True,
                                      'subject': 'S01', 'experiment': 'p300'})
        self.assertTrue(args.lsl)
        self.assertEqual(args.lsl_name, 'g.Nautilus')
        self.assertTrue(args.save)
        self.assertEqual((args.subject, args.experiment), ('S01', 'p300'))
        self.assertEqual((config.n_rows, config.n_cols), (3, 3))
        self.assertEqual(config.n_repetitions, 5)
        self.assertEqual(config.missing_symbols(config.calibration_letters), [])


if __name__ == '__main__':
    unittest.main()
