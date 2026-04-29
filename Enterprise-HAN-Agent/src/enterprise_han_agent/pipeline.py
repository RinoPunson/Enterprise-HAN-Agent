"""Public pipeline API for Enterprise-HAN-Agent."""

from __future__ import annotations

from .agents import ActionAgent, DataExtractorAgent, HANReasoningAgent


class EnterpriseHANPipeline:
    def __init__(
        self,
        extractor_agent: DataExtractorAgent | None = None,
        reasoning_agent: HANReasoningAgent | None = None,
        action_agent: ActionAgent | None = None,
    ) -> None:
        self.extractor_agent = extractor_agent or DataExtractorAgent()
        self.reasoning_agent = reasoning_agent or HANReasoningAgent()
        self.action_agent = action_agent or ActionAgent()

    def analyze(self, text: str, target_company: str | None = None) -> dict:
        extraction = self.extractor_agent.run(text)
        analysis = self.reasoning_agent.run(extraction, text, target_company)
        return self.action_agent.run(analysis)

