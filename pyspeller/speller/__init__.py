"""The P300 speller: matrix, presentation, rendering and online processing."""
from .matrix import SpellerMatrix
from .sigproc import SignalProcessor
from .stimulus import SpellerStimulus

__all__ = ['SpellerMatrix', 'SpellerStimulus', 'SignalProcessor']
