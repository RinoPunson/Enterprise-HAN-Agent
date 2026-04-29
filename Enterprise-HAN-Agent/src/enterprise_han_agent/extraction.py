"""Rule-based extraction baseline for enterprise heterogeneous graphs.

The implementation is intentionally dependency-free. It can be replaced by an
LLM extractor, NER model, or OpenClaw tool adapter without changing the
downstream graph reasoning interface.
"""

from __future__ import annotations

import re
from collections import OrderedDict

from .models import Entity, ExtractionResult, NodeType, Relation, RelationType


COMPANY_SUFFIXES = (
    "有限责任公司",
    "股份有限公司",
    "集团有限公司",
    "控股有限公司",
    "科技有限公司",
    "电子有限公司",
    "材料有限公司",
    "能源有限公司",
    "汽车有限公司",
    "医药有限公司",
    "有限公司",
    "集团",
    "公司",
)
COMPANY_PATTERN = re.compile(
    rf"[\u4e00-\u9fa5A-Za-z0-9]{{2,32}}?(?:{'|'.join(COMPANY_SUFFIXES)})"
)
EXECUTIVE_PATTERN = re.compile(
    r"(?:董事长|总经理|CEO|CFO|CTO|首席执行官|财务负责人|实际控制人|创始人|高管)[：: ]?([\u4e00-\u9fa5A-Za-z]{2,12})"
)
PRODUCT_KEYWORDS = [
    "锂",
    "碳酸锂",
    "电池",
    "芯片",
    "晶圆",
    "传感器",
    "模组",
    "核心部件",
    "原材料",
    "正极材料",
    "负极材料",
    "光伏组件",
    "汽车零部件",
    "服务器",
    "GPU",
    "算力卡",
]

RELATION_KEYWORDS: list[tuple[RelationType, tuple[str, ...]]] = [
    (RelationType.SUPPLIES, ("供应", "供货", "断供", "交付", "采购")),
    (RelationType.DEPENDS_ON, ("依赖", "受制于", "绑定", "核心原材料")),
    (RelationType.PRODUCES, ("生产", "制造", "代工", "产能", "扩产")),
    (RelationType.INVESTS_IN, ("投资", "参股", "控股", "收购")),
    (RelationType.MANAGES, ("任命", "管理", "担任", "离任", "辞任")),
    (RelationType.PARTNERS_WITH, ("合作", "战略协议", "联合", "签约")),
    (RelationType.AFFECTS, ("涨价", "下跌", "受压", "违约", "预警", "风险")),
]


def _unique_entities(entities: list[Entity]) -> list[Entity]:
    unique: OrderedDict[str, Entity] = OrderedDict()
    for entity in entities:
        if entity.name and entity.key not in unique:
            unique[entity.key] = entity
    return list(unique.values())


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。；;！!\n]+", text) if part.strip()]


def _clean_company_name(raw_name: str) -> str:
    name = raw_name.strip(" ，,。；;：:")
    cue_words = (
        "上游",
        "下游",
        "目标",
        "导致",
        "引发",
        "以及",
        "同时",
        "长期供应",
        "长期采购",
        "供应",
        "采购",
        "担任",
        "任职于",
    )
    changed = True
    while changed:
        changed = False
        for cue in cue_words:
            if name.startswith(cue) and len(name) > len(cue) + 2:
                name = name[len(cue) :]
                changed = True

    for cue in ("供应", "采购", "导致", "引发", "担任", "任职于"):
        if cue in name:
            tail = name.split(cue)[-1]
            if any(tail.endswith(suffix) for suffix in COMPANY_SUFFIXES):
                name = tail

    return name


class RuleBasedExtractor:
    """Extracts companies, executives, products, and coarse relations."""

    def extract(self, text: str) -> ExtractionResult:
        entities: list[Entity] = []
        relations: list[Relation] = []

        for sentence in _sentences(text):
            companies = [
                Entity(_clean_company_name(match.group(0)), NodeType.COMPANY, sentence)
                for match in COMPANY_PATTERN.finditer(sentence)
            ]
            executives = [
                Entity(match.group(1), NodeType.EXECUTIVE, sentence)
                for match in EXECUTIVE_PATTERN.finditer(sentence)
            ]
            products = [
                Entity(keyword, NodeType.PRODUCT, sentence)
                for keyword in PRODUCT_KEYWORDS
                if keyword in sentence
            ]

            entities.extend(companies)
            entities.extend(executives)
            entities.extend(products)

            relations.extend(self._relations_from_sentence(sentence, companies, executives, products))

        return ExtractionResult(entities=_unique_entities(entities), relations=relations)

    def _relations_from_sentence(
        self,
        sentence: str,
        companies: list[Entity],
        executives: list[Entity],
        products: list[Entity],
    ) -> list[Relation]:
        relations: list[Relation] = []
        relation_type = self._detect_relation(sentence)

        if len(companies) >= 2:
            for left, right in zip(companies, companies[1:]):
                relations.append(Relation(left, relation_type, right, sentence, self._relation_weight(sentence)))

        for company in companies:
            for product in products:
                product_relation = self._product_relation(sentence)
                if product_relation in {RelationType.SUPPLIES, RelationType.PRODUCES}:
                    relations.append(Relation(company, product_relation, product, sentence, self._relation_weight(sentence)))
                else:
                    relations.append(Relation(company, product_relation, product, sentence, self._relation_weight(sentence)))

            for executive in executives:
                relations.append(Relation(company, RelationType.MANAGES, executive, sentence, self._relation_weight(sentence)))

        if len(companies) >= 2 and products:
            for product in products:
                relations.append(Relation(companies[0], RelationType.SUPPLIES, product, sentence, self._relation_weight(sentence)))
                relations.append(Relation(product, RelationType.DEPENDS_ON, companies[-1], sentence, self._relation_weight(sentence)))

        if len(companies) >= 2 and executives:
            for executive in executives:
                relations.append(Relation(companies[0], RelationType.MANAGES, executive, sentence, self._relation_weight(sentence)))
                relations.append(Relation(executive, RelationType.MANAGES, companies[-1], sentence, self._relation_weight(sentence)))

        return relations

    def _detect_relation(self, sentence: str) -> RelationType:
        for relation_type, keywords in RELATION_KEYWORDS:
            if any(keyword in sentence for keyword in keywords):
                return relation_type
        return RelationType.AFFECTS

    def _product_relation(self, sentence: str) -> RelationType:
        if any(keyword in sentence for keyword in ("供应", "供货", "断供", "采购")):
            return RelationType.SUPPLIES
        if any(keyword in sentence for keyword in ("生产", "制造", "代工", "产能")):
            return RelationType.PRODUCES
        return RelationType.DEPENDS_ON

    def _relation_weight(self, sentence: str) -> float:
        risk_terms = ("断供", "涨价", "违约", "预警", "受压", "下滑", "离任", "减持", "调查")
        return 1.0 + sum(0.25 for term in risk_terms if term in sentence)
