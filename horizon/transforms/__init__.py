"""Transform modules for Horizon SDK."""

from __future__ import annotations

import importlib.util
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Expose concrete types to static analysis while keeping runtime imports lazy.
    from horizon.transforms.anchor_selector import (  # noqa: F401
        AnchorSelector,
        AnchorStrategy,
        AnchorWeights,
        DataPattern,
        calculate_information_score,
        compute_item_hash,
    )
    from horizon.transforms.base import Transform  # noqa: F401
    from horizon.transforms.cache_aligner import CacheAligner  # noqa: F401
    from horizon.transforms.code_compressor import (  # noqa: F401
        CodeAwareCompressor,
        CodeCompressionResult,
        CodeCompressorConfig,
        CodeLanguage,
        DocstringMode,
        detect_language,
        is_tree_sitter_available,
    )
    from horizon.transforms.content_detector import (  # noqa: F401
        ContentType,
        DetectionResult,
        detect_content_type,
    )
    from horizon.transforms.content_router import (  # noqa: F401
        CompressionStrategy,
        ContentRouter,
        ContentRouterConfig,
        RouterCompressionResult,
    )
    from horizon.transforms.diff_compressor import (  # noqa: F401
        DiffCompressionResult,
        DiffCompressor,
        DiffCompressorConfig,
    )
    from horizon.transforms.html_extractor import (  # noqa: F401
        HTMLExtractionResult,
        HTMLExtractor,
        HTMLExtractorConfig,
        is_html_content,
    )
    from horizon.transforms.log_compressor import (  # noqa: F401
        LogCompressionResult,
        LogCompressor,
        LogCompressorConfig,
    )
    from horizon.transforms.pipeline import TransformPipeline  # noqa: F401
    from horizon.transforms.search_compressor import (  # noqa: F401
        SearchCompressionResult,
        SearchCompressor,
        SearchCompressorConfig,
    )
    from horizon.transforms.smart_crusher import SmartCrusher, SmartCrusherConfig  # noqa: F401
    from horizon.transforms.tabular_ingest import (  # noqa: F401
        TabularCompressionResult,
        TabularCompressor,
        TabularCompressorConfig,
    )

_HTML_EXTRACTOR_AVAILABLE = importlib.util.find_spec("trafilatura") is not None

__all__ = [
    # Base
    "Transform",
    "TransformPipeline",
    # Anchor selection
    "AnchorSelector",
    "AnchorStrategy",
    "AnchorWeights",
    "DataPattern",
    "calculate_information_score",
    "compute_item_hash",
    # JSON compression
    "SmartCrusher",
    "SmartCrusherConfig",
    # Text compression (coding tasks)
    "ContentType",
    "DetectionResult",
    "detect_content_type",
    "SearchCompressor",
    "SearchCompressorConfig",
    "SearchCompressionResult",
    "LogCompressor",
    "LogCompressorConfig",
    "LogCompressionResult",
    "TabularCompressor",
    "TabularCompressorConfig",
    "TabularCompressionResult",
    "DiffCompressor",
    "DiffCompressorConfig",
    "DiffCompressionResult",
    # Code-aware compression (AST-based)
    "CodeAwareCompressor",
    "CodeCompressorConfig",
    "CodeCompressionResult",
    "CodeLanguage",
    "DocstringMode",
    "detect_language",
    "is_tree_sitter_available",
    # Content routing
    "ContentRouter",
    "ContentRouterConfig",
    "RouterCompressionResult",
    "CompressionStrategy",
    # Other transforms
    "CacheAligner",
    # HTML extraction (optional)
    "_HTML_EXTRACTOR_AVAILABLE",
]

# Conditionally add HTML extractor exports
if _HTML_EXTRACTOR_AVAILABLE:
    __all__.extend(
        [
            "HTMLExtractor",
            "HTMLExtractorConfig",
            "HTMLExtractionResult",
            "is_html_content",
        ]
    )

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Base
    "Transform": ("horizon.transforms.base", "Transform"),
    "TransformPipeline": ("horizon.transforms.pipeline", "TransformPipeline"),
    # Anchor selection
    "AnchorSelector": ("horizon.transforms.anchor_selector", "AnchorSelector"),
    "AnchorStrategy": ("horizon.transforms.anchor_selector", "AnchorStrategy"),
    "AnchorWeights": ("horizon.transforms.anchor_selector", "AnchorWeights"),
    "DataPattern": ("horizon.transforms.anchor_selector", "DataPattern"),
    "calculate_information_score": (
        "horizon.transforms.anchor_selector",
        "calculate_information_score",
    ),
    "compute_item_hash": ("horizon.transforms.anchor_selector", "compute_item_hash"),
    # JSON compression
    "SmartCrusher": ("horizon.transforms.smart_crusher", "SmartCrusher"),
    "SmartCrusherConfig": ("horizon.transforms.smart_crusher", "SmartCrusherConfig"),
    # Text compression (coding tasks)
    "ContentType": ("horizon.transforms.content_detector", "ContentType"),
    "DetectionResult": ("horizon.transforms.content_detector", "DetectionResult"),
    "detect_content_type": ("horizon.transforms.content_detector", "detect_content_type"),
    "SearchCompressor": ("horizon.transforms.search_compressor", "SearchCompressor"),
    "SearchCompressorConfig": (
        "horizon.transforms.search_compressor",
        "SearchCompressorConfig",
    ),
    "SearchCompressionResult": (
        "horizon.transforms.search_compressor",
        "SearchCompressionResult",
    ),
    "LogCompressor": ("horizon.transforms.log_compressor", "LogCompressor"),
    "LogCompressorConfig": ("horizon.transforms.log_compressor", "LogCompressorConfig"),
    "LogCompressionResult": ("horizon.transforms.log_compressor", "LogCompressionResult"),
    "TabularCompressor": ("horizon.transforms.tabular_ingest", "TabularCompressor"),
    "TabularCompressorConfig": (
        "horizon.transforms.tabular_ingest",
        "TabularCompressorConfig",
    ),
    "TabularCompressionResult": (
        "horizon.transforms.tabular_ingest",
        "TabularCompressionResult",
    ),
    "DiffCompressor": ("horizon.transforms.diff_compressor", "DiffCompressor"),
    "DiffCompressorConfig": ("horizon.transforms.diff_compressor", "DiffCompressorConfig"),
    "DiffCompressionResult": (
        "horizon.transforms.diff_compressor",
        "DiffCompressionResult",
    ),
    # Code-aware compression (AST-based)
    "CodeAwareCompressor": ("horizon.transforms.code_compressor", "CodeAwareCompressor"),
    "CodeCompressorConfig": ("horizon.transforms.code_compressor", "CodeCompressorConfig"),
    "CodeCompressionResult": (
        "horizon.transforms.code_compressor",
        "CodeCompressionResult",
    ),
    "CodeLanguage": ("horizon.transforms.code_compressor", "CodeLanguage"),
    "DocstringMode": ("horizon.transforms.code_compressor", "DocstringMode"),
    "detect_language": ("horizon.transforms.code_compressor", "detect_language"),
    "is_tree_sitter_available": (
        "horizon.transforms.code_compressor",
        "is_tree_sitter_available",
    ),
    # Content routing
    "ContentRouter": ("horizon.transforms.content_router", "ContentRouter"),
    "ContentRouterConfig": ("horizon.transforms.content_router", "ContentRouterConfig"),
    "RouterCompressionResult": (
        "horizon.transforms.content_router",
        "RouterCompressionResult",
    ),
    "CompressionStrategy": ("horizon.transforms.content_router", "CompressionStrategy"),
    # Other transforms
    "CacheAligner": ("horizon.transforms.cache_aligner", "CacheAligner"),
    # HTML extraction (optional dependency - requires trafilatura)
    "HTMLExtractor": ("horizon.transforms.html_extractor", "HTMLExtractor"),
    "HTMLExtractorConfig": ("horizon.transforms.html_extractor", "HTMLExtractorConfig"),
    "HTMLExtractionResult": ("horizon.transforms.html_extractor", "HTMLExtractionResult"),
    "is_html_content": ("horizon.transforms.html_extractor", "is_html_content"),
}


def __getattr__(name: str) -> object:
    if name == "__path__":
        raise AttributeError(name)
    if name == "_HTML_EXTRACTOR_AVAILABLE":
        return _HTML_EXTRACTOR_AVAILABLE

    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
