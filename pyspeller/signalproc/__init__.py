"""Signal processing: pre-processing, epoching and ERP classification."""
from .classifier import ERPClassifier, ShrinkageLDA, auc
from .epochs import EpochGatherer, slice_epochs

__all__ = ['ERPClassifier', 'ShrinkageLDA', 'auc', 'EpochGatherer', 'slice_epochs']
