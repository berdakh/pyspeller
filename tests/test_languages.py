# -*- coding: utf-8 -*-
"""Speller matrices and on-screen text in other languages."""
import unittest

from pyspeller.config import (LAYOUT_LANGUAGE, SYMBOLS_KK_CYRILLIC,
                              SYMBOLS_RU_CYRILLIC, SpellerConfig)
from pyspeller.speller import messages, text as speller_text
from pyspeller.speller.matrix import SpellerMatrix

KAZAKH_ALPHABET = 'АӘБВГҒДЕЁЖЗИЙКҚЛМНҢОӨПРСТУҰҮФХҺЦЧШЩЪЫІЬЭЮЯ'
RUSSIAN_ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'


class TestKazakhMatrix(unittest.TestCase):
    def test_it_holds_the_whole_kazakh_alphabet(self):
        symbols = [s for row in SYMBOLS_KK_CYRILLIC for s in row]
        self.assertEqual(len(KAZAKH_ALPHABET), 42)
        for letter in KAZAKH_ALPHABET:
            self.assertIn(letter, symbols)

    def test_it_has_the_keys_needed_to_write_with(self):
        symbols = [s for row in SYMBOLS_KK_CYRILLIC for s in row]
        for key in (speller_text.SPACE, speller_text.DELETE, speller_text.CLEAR,
                    '.', ','):
            self.assertIn(key, symbols)

    def test_every_cell_is_used_once(self):
        symbols = [s for row in SYMBOLS_KK_CYRILLIC for s in row]
        self.assertEqual(len(symbols), 48)          # 6 rows of 8
        self.assertEqual(len(set(symbols)), 48)

    def test_it_is_a_working_speller_matrix(self):
        matrix = SpellerMatrix(SYMBOLS_KK_CYRILLIC)
        self.assertEqual((matrix.n_rows, matrix.n_cols), (6, 8))
        self.assertEqual(len(matrix.groups), 14)
        row, column = matrix.position_of('Қ')
        self.assertEqual(matrix.symbol_at(row, column), 'Қ')
        scores = {('row', row): 2.0, ('col', column): 2.0}
        self.assertEqual(matrix.decode(scores)[0], 'Қ')

    def test_a_kazakh_word_is_typed_letter_by_letter(self):
        self.assertEqual(speller_text.spell('СӘЛЕМ'), 'СӘЛЕМ')
        self.assertEqual(speller_text.spell(['И', 'Ә', '_', 'Ж', 'О', 'Қ']), 'ИӘ ЖОҚ')
        self.assertEqual(speller_text.spell(['Б', 'А', 'Х', 'DEL', 'Қ']), 'БАҚ')


class TestRussianMatrix(unittest.TestCase):
    def test_it_holds_the_russian_alphabet_and_the_editing_keys(self):
        symbols = [s for row in SYMBOLS_RU_CYRILLIC for s in row]
        self.assertEqual(len(symbols), 36)
        for letter in RUSSIAN_ALPHABET:
            self.assertIn(letter, symbols)
        self.assertIn(speller_text.DELETE, symbols)
        self.assertIn(speller_text.SPACE, symbols)


class TestMessages(unittest.TestCase):
    def test_every_language_says_everything(self):
        keys = set(messages.ENGLISH)
        for name, table in messages.LANGUAGES.items():
            with self.subTest(language=name):
                self.assertEqual(set(table), keys)

    def test_the_formats_take_the_same_arguments(self):
        for name in messages.LANGUAGES:
            with self.subTest(language=name):
                self.assertIn('Қ', messages.say(name, 'look_at', 'Қ'))
                self.assertIn('4', messages.say(name, 'spelled_correctly', 4, 5))
                self.assertTrue(messages.say(name, 'paused'))

    def test_an_unknown_language_falls_back_to_english(self):
        self.assertEqual(messages.say('xx', 'paused'), 'paused')


class TestLayoutAndLanguageTogether(unittest.TestCase):
    def test_choosing_the_kazakh_matrix_brings_kazakh_instructions(self):
        config = SpellerConfig()
        config.use_layout('kk')
        self.assertEqual(config.language, 'kk')
        self.assertEqual((config.n_rows, config.n_cols), (6, 8))
        self.assertEqual(LAYOUT_LANGUAGE['kk'], 'kk')

    def test_the_words_follow_the_matrix(self):
        config = SpellerConfig()
        config.use_layout('kk')
        self.assertEqual(config.missing_symbols(config.calibration_letters), [])
        self.assertEqual(config.missing_symbols(config.feedback_letters), [])
        self.assertEqual(''.join(config.feedback_letters), 'СӘЛЕМ')

    def test_the_language_can_be_chosen_against_the_matrix(self):
        config = SpellerConfig()
        config.use_layout('kk', language='ru')
        self.assertEqual(config.language, 'ru')

    def test_the_stimulus_speaks_the_configured_language(self):
        from pyspeller.speller.stimulus import SpellerStimulus
        config = SpellerConfig()
        config.use_layout('kk')
        stimulus = SpellerStimulus.__new__(SpellerStimulus)   # no buffer needed
        stimulus.config = config
        self.assertEqual(stimulus.say('paused'), messages.KAZAKH['paused'])
        self.assertIn('Қ', stimulus.say('look_at', 'Қ'))


if __name__ == '__main__':
    unittest.main()
