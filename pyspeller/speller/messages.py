# -*- coding: utf-8 -*-
"""What the participant reads on screen, in the language they speak.

Only the participant-facing strings are translated: the cue, the feedback and
the state of the run.  The operator's control panel stays in english, since it
is read by whoever runs the session rather than by the person spelling.

Adding a language is adding one dictionary here; every key must be present, and
a test checks that.
"""

ENGLISH = {
    'look_at': 'look at: %s',
    'calibration': 'calibration: %s',
    'calibration_done': 'calibration done',
    'calibration_stopped': 'calibration stopped after %d letters',
    'practice': 'practice',
    'practice_done': 'practice done',
    'practice_stopped': 'practice stopped',
    'paused': 'paused',
    'no_prediction': 'no prediction',
    'predicted': 'predicted: %s',
    'spelled_correctly': 'spelled %d/%d correctly',
    'stopped_after': 'stopped after %d letters',
    'free_spelling': 'free spelling',
    'typed': 'typed: %s',
}

# Kazakh (Cyrillic).  Written by a non-native speaker: have a native speaker
# read it over before a real session, it is one dictionary to correct.
KAZAKH = {
    'look_at': 'қараңыз: %s',
    'calibration': 'калибрлеу: %s',
    'calibration_done': 'калибрлеу аяқталды',
    'calibration_stopped': 'калибрлеу %d әріптен кейін тоқтатылды',
    'practice': 'жаттығу',
    'practice_done': 'жаттығу аяқталды',
    'practice_stopped': 'жаттығу тоқтатылды',
    'paused': 'кідіріс',
    'no_prediction': 'болжам жоқ',
    'predicted': 'болжам: %s',
    'spelled_correctly': '%d/%d әріп дұрыс терілді',
    'stopped_after': '%d әріптен кейін тоқтатылды',
    'free_spelling': 'еркін теру',
    'typed': 'терілген: %s',
}

RUSSIAN = {
    'look_at': 'смотрите на: %s',
    'calibration': 'калибровка: %s',
    'calibration_done': 'калибровка завершена',
    'calibration_stopped': 'калибровка остановлена после %d букв',
    'practice': 'тренировка',
    'practice_done': 'тренировка завершена',
    'practice_stopped': 'тренировка остановлена',
    'paused': 'пауза',
    'no_prediction': 'нет решения',
    'predicted': 'выбрано: %s',
    'spelled_correctly': 'правильно набрано %d/%d',
    'stopped_after': 'остановлено после %d букв',
    'free_spelling': 'свободный набор',
    'typed': 'набрано: %s',
}

LANGUAGES = {'en': ENGLISH, 'kk': KAZAKH, 'ru': RUSSIAN}


def messages(language='en'):
    """The message table for a language, falling back to english."""
    return LANGUAGES.get(language, ENGLISH)


def say(language, key, *args):
    """One message, formatted -- `say('kk', 'look_at', 'Ә')`."""
    template = messages(language).get(key) or ENGLISH[key]
    return template % args if args else template
