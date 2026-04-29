"""Agent-style wrappers around extraction, graph construction, and actioning."""

from __future__ import annotations

from .extraction import RuleBasedExtractor
from .graph import HeterogeneousGraph
from .models import AnalysisResult, ExtractionResult
from .reasoning import HANReasoner


class DataExtractorAgent:
    def __init__(self, extractor: RuleBasedExtractor | None = None) -> None:
        self.extractor = extractor or RuleBasedExtractor()

    def run(self, text: str) -> ExtractionResult:
        return self.extractor.extract(text)


class HANReasoningAgent:
    def __init__(self, reasoner: HANReasoner | None = None) -> None:
        self.reasoner = reasoner or HANReasoner()

    def run(self, extraction: ExtractionResult, text: str, target_company: str | None = None) -> AnalysisResult:
        graph = HeterogeneousGraph.from_parts(extraction.entities, extraction.relations)
        return self.reasoner.analyze(graph, text, target_company)


class ActionAgent:
    """Converts analysis results into strict downstream JSON."""

    def run(self, result: AnalysisResult) -> dict:
        return result.to_dict()

