"""HAN-inspired meta-path scoring and risk synthesis."""

from __future__ import annotations

import math

from .graph import HeterogeneousGraph
from .models import AnalysisResult, Entity, MetaPathScore, NodeType, Relation


SUPPLY_CHAIN_TERMS = ("供应", "供货", "断供", "涨价", "交付", "产能", "采购", "原材料", "部件")
EXECUTIVE_TERMS = ("高管", "董事长", "CEO", "CFO", "离任", "辞任", "减持", "利益输送", "关联交易")
HIGH_RISK_TERMS = ("断供", "违约", "调查", "暴雷", "下滑", "亏损", "预警", "制裁", "停产", "减持")


class HANReasoner:
    """Scores meta-paths with a lightweight attention approximation."""

    METAPATHS = {
        "Phi_1": (
            [NodeType.COMPANY, NodeType.PRODUCT, NodeType.COMPANY],
            "Company -> Product -> Company (供应链级联传导路径)",
        ),
        "Phi_2": (
            [NodeType.COMPANY, NodeType.EXECUTIVE, NodeType.COMPANY],
            "Company -> Executive -> Company (高管利益输送/人事变动路径)",
        ),
    }

    def analyze(self, graph: HeterogeneousGraph, text: str, target_company: str | None = None) -> AnalysisResult:
        target = graph.find_company(target_company)
        if target is None:
            return AnalysisResult(
                target_company=target_company or "Unknown",
                risk_score=3,
                primary_meta_path="No valid company meta-path detected",
                cascade_reasoning_chain=["Step 1: 输入文本未识别到明确企业节点，建议补充企业名称、产品和关系证据"],
                suggested_action="补充结构化企业名称和上下游关系后重新评估。",
            )

        scores = self.score_metapaths(graph, target, text)
        primary = max(scores, key=lambda item: item.score)
        cascade = self._cascade_reasoning(graph, target)
        risk_score = self._risk_score(text, primary.score, cascade)
        action = self._suggest_action(risk_score, primary.description)

        return AnalysisResult(
            target_company=target.name,
            risk_score=risk_score,
            primary_meta_path=primary.description,
            cascade_reasoning_chain=cascade,
            suggested_action=action,
        )

    def score_metapaths(self, graph: HeterogeneousGraph, target: Entity, text: str) -> list[MetaPathScore]:
        results: list[MetaPathScore] = []
        for name, (node_types, description) in self.METAPATHS.items():
            relation_paths = graph.metapath_paths(target, node_types)
            base_score = sum(self._path_attention(path, text, description) for path in relation_paths)
            semantic_boost = self._semantic_boost(text, description)
            score = base_score + semantic_boost
            results.append(
                MetaPathScore(
                    name=name,
                    description=description,
                    score=score,
                    matched_paths=[self._path_to_nodes(path, target) for path in relation_paths],
                )
            )
        return results

    def _path_attention(self, path: list[Relation], text: str, description: str) -> float:
        if not path:
            return 0.0
        raw = sum(edge.weight for edge in path) / math.sqrt(len(path))
        if "Product" in description:
            raw += sum(0.2 for term in SUPPLY_CHAIN_TERMS if term in text)
        if "Executive" in description:
            raw += sum(0.2 for term in EXECUTIVE_TERMS if term in text)
        return raw

    def _semantic_boost(self, text: str, description: str) -> float:
        terms = SUPPLY_CHAIN_TERMS if "Product" in description else EXECUTIVE_TERMS
        return sum(0.45 for term in terms if term in text)

    def _risk_score(self, text: str, primary_score: float, cascade: list[str]) -> int:
        keyword_score = sum(1 for term in HIGH_RISK_TERMS if term in text)
        cascade_score = min(len(cascade), 4)
        score = 2 + keyword_score + cascade_score + round(min(primary_score, 5))
        return max(1, min(10, score))

    def _cascade_reasoning(self, graph: HeterogeneousGraph, target: Entity) -> list[str]:
        cascade_paths = graph.cascade_paths(target)
        if not cascade_paths:
            return [f"Step 1: {target.name} -> 风险事件 (未发现足够的多跳关系证据，需接入更多上下游数据)"]

        strongest = max(cascade_paths, key=lambda path: sum(edge.weight for edge in path))
        chain = []
        for index, edge in enumerate(strongest, start=1):
            chain.append(
                f"Step {index}: {edge.source.name} -> {edge.target.name} "
                f"({edge.relation.value}; 证据: {self._short_evidence(edge.evidence)})"
            )
        return chain

    def _suggest_action(self, risk_score: int, primary_meta_path: str) -> str:
        if risk_score >= 8:
            return f"触发红色预警，优先核查 {primary_meta_path}，冻结新增授信并启动供应链/治理穿透尽调。"
        if risk_score >= 5:
            return f"触发橙色预警，持续监控 {primary_meta_path}，要求补充上下游合同、库存与高管变动证明。"
        return f"保持常规监控，围绕 {primary_meta_path} 建立周度异动跟踪。"

    def _path_to_nodes(self, path: list[Relation], target: Entity) -> list[str]:
        nodes = [target.name]
        nodes.extend(edge.target.name for edge in path)
        return nodes

    def _short_evidence(self, evidence: str, limit: int = 36) -> str:
        clean = " ".join(evidence.split())
        return clean if len(clean) <= limit else f"{clean[:limit]}..."

