"""Acquisition clients: simulated amplifier and a Lab Streaming Layer bridge."""
from .simulator import EEGSimulator

__all__ = ['EEGSimulator', 'LSLBridge']


def __getattr__(name):     # keep pylsl an optional dependency
    if name == 'LSLBridge':
        from .lsl_bridge import LSLBridge
        return LSLBridge
    raise AttributeError(name)
