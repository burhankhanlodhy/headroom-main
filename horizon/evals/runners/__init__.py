"""Evaluation runners for different scenarios."""

from horizon.evals.runners.before_after import BeforeAfterRunner
from horizon.evals.runners.compression_only import CompressionOnlyRunner

__all__ = ["BeforeAfterRunner", "CompressionOnlyRunner"]
