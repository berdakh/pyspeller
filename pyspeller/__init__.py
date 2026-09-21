"""A minimal, pure-python BCI framework and P300 speller.

The pieces mirror the buffer_bci architecture:

    pyspeller.buffer        the data/event server and its client
    pyspeller.acquisition   amplifier clients (simulator, LSL bridge for g.tec)
    pyspeller.signalproc    pre-processing, epoching, ERP classification
    pyspeller.speller       stimulus presentation and the online BCI loop
    pyspeller.gui           tk control panel with real-time visualisation
"""
from .config import SpellerConfig
from .experiment import LocalExperiment, run_demo

__version__ = '0.1.0'
__all__ = ['SpellerConfig', 'LocalExperiment', 'run_demo']
