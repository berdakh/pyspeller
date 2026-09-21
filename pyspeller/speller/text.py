"""The text field of the speller: turning decoded symbols into typed text.

A commercial speller's matrix holds more than letters -- a space, a backspace,
a way to clear the line -- so the decoded symbol is not always a character to
append.  Keeping that in one place means the speller window, the control panel
and any other client agree on what has been typed.
"""

SPACE = '_'
DELETE = 'DEL'      # backspace: rub out the last letter the speller got wrong
CLEAR = 'CLR'       # wipe the whole line

#: symbols that act on the text instead of being inserted into it
CONTROL_KEYS = (SPACE, DELETE, CLEAR)

#: event a client sends to correct the text without the user selecting a key
#: (the control panel's backspace button, a carer's keyboard, another app)
EDIT_EVENT = 'speller.edit'

#: event that interrupts a running block: 'pause', 'resume' or 'stop'
CONTROL_EVENT = 'speller.control'
PAUSE, RESUME, STOP = 'pause', 'resume', 'stop'


def apply_symbol(text, symbol):
    """The text after the speller decoded `symbol`."""
    if symbol is None:
        return text
    symbol = str(symbol)
    if symbol == DELETE:
        return text[:-1]
    if symbol == CLEAR:
        return ''
    if symbol == SPACE:
        return text + ' '
    return text + symbol


def spell(symbols, text=''):
    """Apply a whole sequence of decoded symbols."""
    for symbol in symbols:
        text = apply_symbol(text, symbol)
    return text


def display(text):
    """The text as it is shown in the speller's field, with a caret."""
    return '%s_' % text
