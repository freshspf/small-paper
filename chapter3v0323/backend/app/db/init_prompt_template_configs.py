from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template_config import PromptTemplateConfig


DEFAULT_PROMPT_TEMPLATE_CONFIGS = [
    {
        "templateName": "第三章基础型提示词",
        "taskType": "ontology_evaluation",
        "templateType": "basic",
        "layerName": None,
        "templateContent": "你是一位本体学习评估专家。请判断给定 RDFS 公理是否正确。\n\n公理：{axiom_text}\n\n请输出：判断结果：[正确/错误]\\n解释：[一句话说明理由]",
        "switchCount": 0,
        "switchDomain": 0,
        "switchNaming": 0,
        "switchEntity": 0,
        "remark": "第三章本体学习能力评估：基础型提示词。",
        "status": 1,
    },
    {
        "templateName": "第三章指令增强型提示词",
        "taskType": "ontology_evaluation",
        "templateType": "instruction_enhanced",
        "layerName": None,
        "templateContent": "你是一位本体学习评估专家。请根据 RDFS 语义规则，分步骤判断给定公理是否正确。\n\n判断步骤：识别公理类型；分析主体、谓词和客体语义；依据 RDFS 规则判断；给出结论。\n\n公理：{axiom_text}\n\n请输出：判断结果：[正确/错误]\\n解释：[基于语义规则的一句话说明]",
        "switchCount": 0,
        "switchDomain": 0,
        "switchNaming": 0,
        "switchEntity": 0,
        "remark": "第三章本体学习能力评估：指令增强型提示词。",
        "status": 1,
    },
    {
        "templateName": "第三章上下文引导型提示词",
        "taskType": "ontology_evaluation",
        "templateType": "context_guided",
        "layerName": None,
        "templateContent": "你是一位本体学习评估专家。请结合背景知识和 RDFS 语义规则判断公理是否正确。\n\n背景知识：{context_info}\n\n公理：{axiom_text}\n\n请输出：判断结果：[正确/错误]\\n解释：[结合背景知识与语义规则的一句话说明]",
        "switchCount": 0,
        "switchDomain": 0,
        "switchNaming": 0,
        "switchEntity": 0,
        "remark": "第三章本体学习能力评估：上下文引导型提示词。",
        "status": 1,
    },
    {
        "templateName": "第四章 baseline 提示词",
        "taskType": "ontology_learning",
        "templateType": "baseline",
        "layerName": "baseline",
        "templateContent": "请直接从输入文本中学习 RDFS 本体公理，输出 subClassOf、subPropertyOf、domain 和 range 四类结果。要求结果基于文本证据，不输出解释性长段落。",
        "switchCount": 0,
        "switchDomain": 0,
        "switchNaming": 0,
        "switchEntity": 0,
        "remark": "第四章本体学习方法：直接抽取 baseline。",
        "status": 1,
    },
    {
        "templateName": "第四章配置优化统一模板",
        "taskType": "ontology_learning",
        "templateType": "configurable",
        "layerName": "ablation",
        "templateContent": "请从输入文本中学习本体术语与 RDFS 公理。请遵循以下可配置约束：\n{SWITCH_MODULES}\n\n输入文本：{input_text}\n\n请输出结构化 JSON。",
        "switchCount": 1,
        "switchDomain": 1,
        "switchNaming": 1,
        "switchEntity": 1,
        "remark": "第四章配置优化实验：基础模板 + 四个开关动态组装。",
        "status": 1,
    },
    {
        "templateName": "语义网络层提示词",
        "taskType": "ontology_learning",
        "templateType": "meaning",
        "layerName": "meaning",
        "templateContent": "请基于论文文本抽取语义网络关系，保留 subject、relation、object、chunk 和 context。请只做抽取，不做同义归并。\n{SWITCH_MODULES}",
        "switchCount": 1,
        "switchDomain": 1,
        "switchNaming": 1,
        "switchEntity": 0,
        "remark": "第一层：聚焦语义关系抽取，不做术语归并。",
        "status": 1,
    },
    {
        "templateName": "术语归并层提示词",
        "taskType": "ontology_learning",
        "templateType": "term",
        "layerName": "term",
        "templateContent": "请对语义网络层输出进行术语精化、同义归并和命名规范化，输出可供概念建模层使用的结构化结果。\n{SWITCH_MODULES}",
        "switchCount": 1,
        "switchDomain": 1,
        "switchNaming": 1,
        "switchEntity": 1,
        "remark": "第二层：基于上一层输出进行术语规范化。",
        "status": 1,
    },
    {
        "templateName": "概念公理层提示词",
        "taskType": "ontology_learning",
        "templateType": "concept",
        "layerName": "concept",
        "templateContent": "请基于术语精化层结果学习 subClassOf、subPropertyOf、domain 和 range 四类 RDFS 公理，允许在证据支持下进行适度概念建模扩展。\n{SWITCH_MODULES}",
        "switchCount": 1,
        "switchDomain": 1,
        "switchNaming": 1,
        "switchEntity": 1,
        "remark": "第三层：输出最终本体公理。",
        "status": 1,
    },
]


def seed_prompt_template_configs(db: Session) -> None:
    existing_templates = {
        template.templateName: template
        for template in db.scalars(select(PromptTemplateConfig))
    }

    for item in DEFAULT_PROMPT_TEMPLATE_CONFIGS:
        existing = existing_templates.get(item["templateName"])
        if existing is None:
            db.add(PromptTemplateConfig(**item))
        elif existing.taskType == "ontology_learning":
            for field, value in item.items():
                setattr(existing, field, value)
            db.add(existing)
    db.commit()
