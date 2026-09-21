"""The tutorial notebook must at least be valid and compile.

Executing it takes half a minute and needs matplotlib, so that is left to
`python -m nbclient docs/pyspeller_tutorial.ipynb`; this keeps it from rotting.
"""
import json
import os
import unittest

NOTEBOOK = os.path.join(os.path.dirname(__file__), '..', 'docs',
                        'pyspeller_tutorial.ipynb')


class TestTutorialNotebook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(NOTEBOOK) as handle:
            cls.notebook = json.load(handle)

    def test_it_is_a_notebook(self):
        self.assertEqual(self.notebook['nbformat'], 4)
        self.assertTrue(self.notebook['cells'])

    def test_every_code_cell_compiles(self):
        for index, cell in enumerate(self.notebook['cells']):
            if cell['cell_type'] != 'code':
                continue
            source = ''.join(cell['source'])
            with self.subTest(cell=index):
                compile(source, '<cell %d>' % index, 'exec')

    def test_it_is_checked_in_without_outputs(self):
        for cell in self.notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertEqual(cell.get('outputs', []), [])
                self.assertIsNone(cell.get('execution_count'))

    def test_it_covers_the_whole_session(self):
        text = json.dumps(self.notebook)
        for step in ('SpellerConfig', 'LocalExperiment', 'calibrate', 'train',
                     'feedback', 'load_session', 'lsl'):
            self.assertIn(step, text)


if __name__ == '__main__':
    unittest.main()
