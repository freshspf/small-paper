"use client";

import { useMemo, useState, useTransition } from "react";

import {
  createPromptTemplateConfig,
  deletePromptTemplateConfig,
  getPromptTemplateConfigsByFilter,
  previewPromptTemplateConfig,
  type PromptTemplateConfigPreview,
  type PromptTemplateConfigPayload,
  setPromptTemplateConfigStatus,
  updatePromptTemplateConfig,
} from "@/lib/api";
import { type PromptTemplateConfigItem } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


type TemplateManagerProps = {
  templates: PromptTemplateConfigItem[];
};

type FormState = {
  templateName: string;
  taskType: string;
  templateType: string;
  layerName: string;
  templateContent: string;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntity: number;
  remark: string;
  status: number;
};


const EMPTY_FORM: FormState = {
  templateName: "",
  taskType: "ontology_learning",
  templateType: "meaning",
  layerName: "meaning",
  templateContent: "",
  switchCount: 0,
  switchDomain: 0,
  switchNaming: 0,
  switchEntity: 0,
  remark: "",
  status: 1,
};

const TASK_TYPE_OPTIONS = [
  { value: "ontology_evaluation", label: "本体评估" },
  { value: "ontology_learning", label: "本体学习" },
  { value: "configuration_optimization", label: "配置优化" },
];

const EVALUATION_TEMPLATE_OPTIONS = [
  { value: "basic", label: "基础型提示词" },
  { value: "instruction_enhanced", label: "指令增强型提示词" },
  { value: "context_guided", label: "上下文引导型提示词" },
];

const LEARNING_TEMPLATE_OPTIONS = [
  { value: "baseline", label: "baseline 提示词" },
  { value: "meaning", label: "语义网络层提示词" },
  { value: "term", label: "术语精化层提示词" },
  { value: "concept", label: "概念建模层提示词" },
];

const CONFIGURATION_TEMPLATE_OPTIONS = [
  { value: "configurable", label: "配置优化统一模板" },
];

const LAYER_OPTIONS = [
  { value: "baseline", label: "baseline" },
  { value: "ablation", label: "配置优化实验" },
  { value: "meaning", label: "语义网络层" },
  { value: "term", label: "术语精化层" },
  { value: "concept", label: "概念建模层" },
];

const EVALUATION_PROMPT_CONTENTS: Record<string, string> = {
  basic: `你是一位本体学习专家，请判断给定的RDFS本体公理是否正确。

任务说明：
RDFS本体公理可能涉及多种语义关系，包括：
- 类之间的关系（subClassOf）
- 属性之间的关系（subPropertyOf）
- 属性的定义域（domain）
- 属性的值域（range）

请结合常识知识、领域知识以及概念和属性之间的语义约束，对公理的合理性进行判断。
如果公理表达的关系不符合常识或语义明显不合理，则判断为“错误”；否则判断为“正确”。

公理：
{axiom_text}

请严格按照以下格式输出（必须完全一致，不要添加任何额外内容）：
判断结果：[正确/错误]
解释：[一句话说明理由]`,
  instruction_enhanced: `你是一位本体学习专家。请根据给定的RDFS语义规则，对本体公理的正确性进行判断。

任务说明：
RDFS本体公理描述类和属性之间的语义关系，主要包括以下四类：

1）子类关系（subClassOf）：
如果类A是类B的子类，则A的所有实例都属于B。

2）子属性关系（subPropertyOf）：
如果属性P是属性Q的子属性，则任意通过P关联的资源对也必须满足Q关系。

3）定义域（domain）：
如果属性P的定义域为类C，则“使用该属性的主体必须属于类C”。

4）值域（range）：
如果属性P的值域为类C，则“该属性的客体必须属于类C”。

判断步骤：
请按照以下步骤进行推理：
（1）识别该公理的类型（subClassOf / subPropertyOf / domain / range）；
（2）根据对应语义规则，判断该关系是否成立；
（3）结合常识知识，判断是否存在明显语义冲突；
（4）给出最终判断结果。

判断标准：
- 如果该公理符合语义规则且符合常识，则判断为“正确”；
- 如果违反语义规则或明显不符合常识，则判断为“错误”。

公理：
{axiom_text}

请严格按照以下格式输出（必须完全一致，不要添加任何额外内容）：
判断结果：[正确/错误]
解释：[基于语义规则的一句话说明]`,
  context_guided: `你是一位本体学习专家。请基于给定的背景知识，对RDFS本体公理进行语义分析与推理，并判断其正确性。

任务说明：
RDFS本体公理用于描述类和属性之间的语义关系，主要包括以下四类：
1）subClassOf：表示类之间的包含关系；
2）subPropertyOf：表示属性之间的包含关系；
3）domain：表示属性的主体应属于某一类；
4）range：表示属性的客体应属于某一类。

背景知识：
{context_info}

请结合上述背景知识、RDFS语义规则以及常识知识，对给定公理进行判断。

推理要求：
请按照以下步骤进行分析：
（1）识别公理中涉及的概念或属性；
（2）结合背景知识分析其语义关系或约束信息；
（3）依据对应的RDFS语义规则进行推理；
（4）判断该公理是否合理；
（5）如果该公理与背景知识或语义规则存在明显冲突，则判定为“错误”。

公理：
{axiom_text}

请严格按照以下格式输出（必须完全一致，不要添加任何额外内容）：
判断结果：[正确/错误]
解释：[结合背景知识与语义规则的一句话说明]`,
};

const CONFIGURABLE_TEMPLATE_CONTENT = "You are an ontology axiom extraction system. Your task is to identify and extract formal RDFS ontology axioms from the given scientific or technical text.\n\n{DOMAIN_HINT}\n\n**CORE INSTRUCTIONS:**\n1. Extract ontology axioms including but not limited to:\n   - Subclass relationships (`rdfs:subClassOf`)\n   - Sub-objectproperty relationships (`owl:subObjectPropertyOf`)\n   - Sub-dataproperty relationships (`owl:subDataPropertyOf`)\n   - Domain restrictions (`rdfs:domain`)\n   - Range restrictions (`rdfs:range`)\n   - Disjointness axioms (`owl:disjointWith`)\n\n2. Each axiom must represent a single atomic ontological assertion and describe the knowledge in the given field.\n\n3. Every axiom MUST be directly supported by an exact quote from the provided text OR logically inferred from explicit statements about class/property relationships.\n\n{COUNT_CONSTRAINT}\n\n{ENTITY_DEFINITION}\n\n{NAMING_RULES}\n\n**OUTPUT FORMAT:**\nReturn a valid JSON object with the following exact structure:\n{\n  \"axioms\": [\n    {\n      \"subject\": \"string (the ontological entity)\",\n      \"relation\": \"string (the ontological predicate)\",\n      \"object\": \"string (the target entity or value)\",\n      \"chunk\": \"string (from which section)\",\n      \"evidence\": \"string (exact text segment supporting this axiom)\"\n    }\n  ]\n}\n\n**EXAMPLES OF EXPECTED EXTRACTION:**\nInput text: \"Aquifer microbes are a subclass of microbial functional guilds. They are found in aquifers.\"\n\nExtracted axioms:\n1. {\n  \"subject\": \"AquiferMicrobes\",\n  \"relation\": \"rdfs:subClassOf\",\n  \"object\": \"MicrobialFunctionalGuild\",\n  \"chunk\": \"ABSTRACT\",\n  \"evidence\": \"Aquifer microbes are a subclass of microbial functional guilds.\"\n}\n2. {\n  \"subject\": \"foundIn\",\n  \"relation\": \"rdfs:domain\",\n  \"object\": \"AquiferMicrobes\",\n  \"chunk\": \"Introduction\",\n  \"evidence\": \"They are found in aquifers.\"\n}\n3. {\n  \"subject\": \"foundIn\",\n  \"relation\": \"rdfs:range\",\n  \"object\": \"Aquifer\",\n  \"chunk\": \"Experiments\",\n  \"evidence\": \"They are found in aquifers.\"\n}\n\n**INPUT TEXT:**\n{text}";

const BASELINE_TEMPLATE_CONTENT = `You are an ontology construction system. Your task is to construct a conservative RDFS ontology directly from a single raw text chunk.

{domain_context}

CORE INSTRUCTIONS:

1. Work only on the current chunk.
   - Do not assume information from other chunks.
   - Do not merge with unseen context.

2. Extract ontology elements conservatively:
   - Classes: abstract concepts explicitly supported by the chunk.
   - Properties: relations explicitly supported by the chunk.

3. Keep the ontology minimal and high-confidence:
   - Use only terms and relations clearly grounded in the chunk.
   - Do not invent additional terms.
   - Do not perform ontology completion.
   - If evidence is weak, omit the axiom.

4. Construct hierarchy very strictly:
   - Infer rdfs:subClassOf only when the chunk explicitly states or very directly implies a subclass relation.
   - Infer rdfs:subPropertyOf only when the chunk clearly supports it.

5. Infer domain and range very strictly:
   - Only assign domain/range when the subject/object typing is explicit in the current chunk.
   - Do not guess missing domain/range.

6. Use consistent naming:
   - Classes in PascalCase.
   - Properties in camelCase.
   - Avoid vague names and unnecessary variants.

7. Output only what the current chunk supports.
   - Conservative extraction is preferred over completeness.

OUTPUT FORMAT:
Return a valid JSON object with the following structure:
{
  "classes": [...],
  "properties": [...],
  "subClassOf": [
    {"sub": "...", "super": "..."}
  ],
  "subPropertyOf": [
    {"sub": "...", "super": "..."}
  ],
  "domain": [
    {"property": "...", "class": "..."}
  ],
  "range": [
    {"property": "...", "class": "..."}
  ]
}

INPUT CHUNK METADATA:
- chunk_id: {chunk_id}
- section_title: {section_title}
- page_start: {page_start}
- page_end: {page_end}

INPUT TEXT CHUNK:
{text}`;

const SWITCH_LABELS = [
  ["switchCount", "数量"] as const,
  ["switchDomain", "领域"] as const,
  ["switchNaming", "命名"] as const,
  ["switchEntity", "实体"] as const,
];


function isEvaluationTask(taskType: string) {
  return taskType === "ontology_evaluation" || taskType === "chapter3_evaluation";
}


function isConfigurationOptimizationTask(taskType: string) {
  return taskType === "configuration_optimization";
}


function formatTaskType(taskType: string) {
  if (isEvaluationTask(taskType)) {
    return "本体评估";
  }
  if (isConfigurationOptimizationTask(taskType)) {
    return "配置优化";
  }
  return "本体学习";
}


function formatTemplateType(templateType: string) {
  const option = [...EVALUATION_TEMPLATE_OPTIONS, ...LEARNING_TEMPLATE_OPTIONS, ...CONFIGURATION_TEMPLATE_OPTIONS].find(
    (item) => item.value === templateType,
  );
  return option?.label ?? templateType;
}


function toFormState(template: PromptTemplateConfigItem): FormState {
  const taskType = isEvaluationTask(template.taskType)
    ? "ontology_evaluation"
    : isConfigurationOptimizationTask(template.taskType)
      ? "configuration_optimization"
      : "ontology_learning";
  return {
    templateName: template.templateName,
    taskType,
    templateType: template.templateType,
    layerName: taskType === "ontology_evaluation" ? "" : template.layerName,
    templateContent: template.templateContent,
    switchCount: taskType === "ontology_evaluation" ? 0 : template.switchCount,
    switchDomain: taskType === "ontology_evaluation" ? 0 : template.switchDomain,
    switchNaming: taskType === "ontology_evaluation" ? 0 : template.switchNaming,
    switchEntity: taskType === "ontology_evaluation" ? 0 : template.switchEntity,
    remark: template.remark,
    status: template.status,
  };
}


function toPayload(formState: FormState): PromptTemplateConfigPayload {
  const isEvaluation = isEvaluationTask(formState.taskType);
  const isConfiguration = isConfigurationOptimizationTask(formState.taskType);
  return {
    templateName: formState.templateName.trim(),
    taskType: isEvaluation ? "ontology_evaluation" : isConfiguration ? "configuration_optimization" : "ontology_learning",
    templateType: isConfiguration ? "configurable" : formState.templateType.trim(),
    layerName: isEvaluation ? null : isConfiguration ? "ablation" : formState.layerName.trim() || null,
    templateContent: formState.templateContent.trim(),
    switchCount: isEvaluation ? 0 : Number(formState.switchCount),
    switchDomain: isEvaluation ? 0 : Number(formState.switchDomain),
    switchNaming: isEvaluation ? 0 : Number(formState.switchNaming),
    switchEntity: isEvaluation ? 0 : Number(formState.switchEntity),
    remark: formState.remark.trim() || null,
    status: Number(formState.status),
  };
}


export function TemplateManager({ templates }: TemplateManagerProps) {
  const [items, setItems] = useState(templates);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTemplateId, setEditingTemplateId] = useState<number | null>(null);
  const [formState, setFormState] = useState<FormState>(EMPTY_FORM);
  const [filters, setFilters] = useState({
    templateName: "",
    taskType: "",
    templateType: "",
    layerName: "",
  });
  const [preview, setPreview] = useState<PromptTemplateConfigPreview | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const activeCount = useMemo(() => items.filter((item) => item.status === 1).length, [items]);
  const switchOnCount = useMemo(
    () =>
      items.reduce(
        (total, item) =>
          total + item.switchCount + item.switchDomain + item.switchNaming + item.switchEntity,
        0,
      ),
    [items],
  );
  const dialogTitle = editingTemplateId === null ? "新增提示词配置" : "编辑提示词配置";

  function openCreateDialog() {
    setEditingTemplateId(null);
    setFormState(EMPTY_FORM);
    setErrorMessage(null);
    setIsDialogOpen(true);
  }

  function openEditDialog(template: PromptTemplateConfigItem) {
    setEditingTemplateId(template.id);
    setFormState(toFormState(template));
    setErrorMessage(null);
    setIsDialogOpen(true);
  }

  function closeDialog() {
    setIsDialogOpen(false);
    setEditingTemplateId(null);
    setFormState(EMPTY_FORM);
    setErrorMessage(null);
  }

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setFormState((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function handleTaskTypeChange(taskType: string) {
    if (isEvaluationTask(taskType)) {
      setFormState((current) => ({
        ...current,
        taskType: "ontology_evaluation",
        templateType: "basic",
        layerName: "",
        templateContent: current.templateContent || EVALUATION_PROMPT_CONTENTS.basic,
        switchCount: 0,
        switchDomain: 0,
        switchNaming: 0,
        switchEntity: 0,
      }));
      return;
    }

    if (isConfigurationOptimizationTask(taskType)) {
      setFormState((current) => ({
        ...current,
        taskType: "configuration_optimization",
        templateName: current.templateName || "第四章配置优化统一模板",
        templateType: "configurable",
        layerName: "ablation",
        templateContent: CONFIGURABLE_TEMPLATE_CONTENT,
        remark: current.remark || "第四章提示词配置优化实验统一模板，包含 COUNT、DOMAIN、NAMING、ENTITY 四类开关占位符。",
      }));
      return;
    }

    setFormState((current) => ({
      ...current,
      taskType: "ontology_learning",
      templateType: "meaning",
      layerName: "meaning",
    }));
  }

  function handleTemplateTypeChange(templateType: string) {
    const isEvaluation = isEvaluationTask(formState.taskType);
    const isConfiguration = isConfigurationOptimizationTask(formState.taskType);
    if (isEvaluation) {
      setFormState((current) => ({
        ...current,
        templateType,
        templateContent: EVALUATION_PROMPT_CONTENTS[templateType] ?? current.templateContent,
      }));
      return;
    }

    if (isConfiguration) {
      setFormState((current) => ({
        ...current,
        templateType: "configurable",
        layerName: "ablation",
        templateContent: CONFIGURABLE_TEMPLATE_CONTENT,
      }));
      return;
    }

    setFormState((current) => ({
      ...current,
      templateType,
      layerName: templateType === "configurable" ? "ablation" : templateType,
      templateName: templateType === "baseline" && !current.templateName ? "第四章 baseline 提示词" : current.templateName,
      templateContent: templateType === "baseline" ? BASELINE_TEMPLATE_CONTENT : current.templateContent,
      remark: templateType === "baseline" && !current.remark ? "第四章本体学习 baseline，一次处理一个 PDF chunk，仅保留 domain_context 动态占位符。" : current.remark,
    }));
  }

  function updateFilter<K extends keyof typeof filters>(key: K, value: (typeof filters)[K]) {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function validatePayload(payload: PromptTemplateConfigPayload) {
    if (!payload.templateName || !payload.taskType || !payload.templateType || !payload.templateContent) {
      return "请填写模板名称、任务类型、模板类型和模板内容。";
    }
    return null;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    const payload = toPayload(formState);
    const validationError = validatePayload(payload);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    startTransition(async () => {
      try {
        if (editingTemplateId === null) {
          const created = await createPromptTemplateConfig(payload);
          setItems((current) => [created, ...current]);
        } else {
          const updated = await updatePromptTemplateConfig(editingTemplateId, payload);
          setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        }
        closeDialog();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "提交失败，请稍后重试。");
      }
    });
  }

  function handleDelete(template: PromptTemplateConfigItem) {
    const confirmed = window.confirm(`确认删除提示词配置“${template.templateName}”吗？`);
    if (!confirmed) {
      return;
    }

    setErrorMessage(null);
    startTransition(async () => {
      try {
        await deletePromptTemplateConfig(template.id);
        setItems((current) => current.filter((item) => item.id !== template.id));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "删除失败，请稍后重试。");
      }
    });
  }

  function toggleStatus(template: PromptTemplateConfigItem) {
    const nextStatus = template.status === 1 ? 0 : 1;
    startTransition(async () => {
      try {
        const updated = await setPromptTemplateConfigStatus(template.id, nextStatus);
        setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "状态切换失败，请稍后重试。");
      }
    });
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getPromptTemplateConfigsByFilter(filters);
        setItems(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "查询失败，请稍后重试。");
      }
    });
  }

  function resetFilters() {
    const emptyFilters = {
      templateName: "",
      taskType: "",
      templateType: "",
      layerName: "",
    };
    setFilters(emptyFilters);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getPromptTemplateConfigsByFilter(emptyFilters);
        setItems(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "查询失败，请稍后重试。");
      }
    });
  }

  function handlePreview(template: PromptTemplateConfigItem) {
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await previewPromptTemplateConfig(template.id);
        setPreview(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "预览失败，请稍后重试。");
      }
    });
  }

  function toggleFormSwitch(key: (typeof SWITCH_LABELS)[number][0]) {
    updateField(key, formState[key] === 1 ? 0 : 1);
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">提示词配置总数</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{items.length}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">启用配置</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{activeCount}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">已打开开关</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{switchOnCount}</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-6 py-5">
          <div>
            <h3 className="text-lg font-semibold text-ink">提示词配置列表</h3>
            <p className="text-sm text-slate-600">维护模板内容、任务层级和四类约束开关。</p>
          </div>
          <Button variant="secondary" onClick={openCreateDialog}>
            新增配置
          </Button>
        </div>

        <form className="grid gap-3 border-b border-line bg-white/40 px-6 py-4 lg:grid-cols-[1.2fr_1fr_1fr_1fr_auto_auto]" onSubmit={handleSearch}>
          <input
            className="paper-input"
            value={filters.templateName}
            onChange={(event) => updateFilter("templateName", event.target.value)}
            placeholder="模板名称"
          />
          <select
            className="paper-input"
            value={filters.taskType}
            onChange={(event) => updateFilter("taskType", event.target.value)}
          >
            <option value="">全部任务类型</option>
            {TASK_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select
            className="paper-input"
            value={filters.templateType}
            onChange={(event) => updateFilter("templateType", event.target.value)}
          >
            <option value="">全部模板类型</option>
            {[...EVALUATION_TEMPLATE_OPTIONS, ...LEARNING_TEMPLATE_OPTIONS, ...CONFIGURATION_TEMPLATE_OPTIONS].map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select
            className="paper-input"
            value={filters.layerName}
            onChange={(event) => updateFilter("layerName", event.target.value)}
          >
            <option value="">全部层名称</option>
            {LAYER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <Button type="submit" variant="secondary" disabled={isPending}>
            查询
          </Button>
          <Button type="button" variant="outline" onClick={resetFilters} disabled={isPending}>
            重置
          </Button>
        </form>

        {errorMessage ? (
          <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div>
        ) : null}

        {items.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-base font-medium text-ink">当前尚未配置提示词</p>
            <p className="mt-2 text-sm text-slate-500">可以点击右上角“新增配置”录入提示词模板。</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="paper-table min-w-[1120px]">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>模板名称</th>
                  <th>任务类型</th>
                  <th>模板类型</th>
                  <th>层名称</th>
                  <th>COUNT</th>
                  <th>DOMAIN</th>
                  <th>NAMING</th>
                  <th>ENTITY</th>
                  <th>状态</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((template) => (
                  <tr key={template.id}>
                    <td>{template.id}</td>
                    <td>
                      <div>
                        <p className="font-medium text-ink">{template.templateName}</p>
                        <p className="mt-1 max-w-[260px] truncate text-xs text-slate-500">
                          {template.remark || "暂无说明"}
                        </p>
                      </div>
                    </td>
                    <td>{formatTaskType(template.taskType)}</td>
                    <td>{formatTemplateType(template.templateType)}</td>
                    <td>{isEvaluationTask(template.taskType) ? "--" : template.layerName || "--"}</td>
                    <td><Badge variant={template.switchCount === 1 ? "success" : "muted"}>{template.switchCount === 1 ? "ON" : "OFF"}</Badge></td>
                    <td><Badge variant={template.switchDomain === 1 ? "success" : "muted"}>{template.switchDomain === 1 ? "ON" : "OFF"}</Badge></td>
                    <td><Badge variant={template.switchNaming === 1 ? "success" : "muted"}>{template.switchNaming === 1 ? "ON" : "OFF"}</Badge></td>
                    <td><Badge variant={template.switchEntity === 1 ? "success" : "muted"}>{template.switchEntity === 1 ? "ON" : "OFF"}</Badge></td>
                    <td>
                      <Badge variant={template.status === 1 ? "success" : "muted"}>
                        {template.status === 1 ? "启用" : "停用"}
                      </Badge>
                    </td>
                    <td>{template.updatedTime}</td>
                    <td>
                      <div className="flex gap-2">
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => handlePreview(template)}>
                          预览
                        </Button>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => openEditDialog(template)}>
                          编辑
                        </Button>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => toggleStatus(template)}>
                          {template.status === 1 ? "停用" : "启用"}
                        </Button>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => handleDelete(template)}>
                          删除
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-5xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">{dialogTitle}</h3>
                <p className="mt-2 text-sm text-slate-600">配置提示词文本和约束开关，供本体学习流程复用。</p>
              </div>
              <Button variant="outline" onClick={closeDialog}>
                关闭
              </Button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div className="grid gap-5 md:grid-cols-3">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模板名称</span>
                  <input
                    className="paper-input"
                    value={formState.templateName}
                    onChange={(event) => updateField("templateName", event.target.value)}
                    placeholder="例如：语义网络层提示词"
                    required
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">任务类型</span>
                  <select
                    className="paper-input"
                    value={formState.taskType}
                    onChange={(event) => handleTaskTypeChange(event.target.value)}
                    required
                  >
                    {TASK_TYPE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模板类型</span>
                  <select
                    className="paper-input"
                    value={formState.templateType}
                    onChange={(event) => handleTemplateTypeChange(event.target.value)}
                  >
                    {(isEvaluationTask(formState.taskType)
                      ? EVALUATION_TEMPLATE_OPTIONS
                      : isConfigurationOptimizationTask(formState.taskType)
                        ? CONFIGURATION_TEMPLATE_OPTIONS
                        : LEARNING_TEMPLATE_OPTIONS
                    ).map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>

                {!isEvaluationTask(formState.taskType) && !isConfigurationOptimizationTask(formState.taskType) ? (
                  <label className="space-y-2">
                    <span className="text-sm font-medium text-ink">层名称</span>
                    <select
                      className="paper-input"
                      value={formState.layerName}
                      onChange={(event) => updateField("layerName", event.target.value)}
                    >
                      {LAYER_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </label>
                ) : null}

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">启用状态</span>
                  <select
                    className="paper-input"
                    value={formState.status}
                    onChange={(event) => updateField("status", Number(event.target.value))}
                  >
                    <option value={1}>启用</option>
                    <option value={0}>停用</option>
                  </select>
                </label>
              </div>

              {!isEvaluationTask(formState.taskType) ? (
                <div className="grid gap-3 md:grid-cols-4">
                  {SWITCH_LABELS.map(([key, label]) => (
                    <div key={key} className="flex items-center justify-between rounded-2xl border border-line bg-white/80 px-4 py-3">
                      <span className="text-sm font-medium text-ink">{label}开关</span>
                      <button
                        type="button"
                        onClick={() => toggleFormSwitch(key)}
                        className={`relative h-7 w-14 rounded-full transition ${
                          formState[key] === 1 ? "bg-sage" : "bg-slate-300"
                        }`}
                        aria-label={`${label}开关`}
                      >
                        <span
                          className={`absolute top-1 h-5 w-5 rounded-full bg-white transition ${
                            formState[key] === 1 ? "left-8" : "left-1"
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-line bg-white/70 px-4 py-3 text-sm text-slate-600">
                  本体评估模板不设置层名称，也不使用 COUNT、DOMAIN、NAMING、ENTITY 开关。
                </div>
              )}

              {isConfigurationOptimizationTask(formState.taskType) ? (
                <div className="rounded-2xl border border-line bg-white/70 px-4 py-3 text-sm leading-6 text-slate-600">
                  配置优化统一模板固定使用第四章 configurable_template.txt。COUNT、NAMING、ENTITY 开关会直接替换对应占位符；DOMAIN 开关会在后续执行本体学习任务时，根据用户选择的 geography、medical 或 transportation 自动填充对应领域模块。
                </div>
              ) : null}

              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">模板说明</span>
                <input
                  className="paper-input"
                  value={formState.remark}
                  onChange={(event) => updateField("remark", event.target.value)}
                  placeholder="用于说明该模板适用的实验层级和约束策略"
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">模板内容</span>
                <textarea
                  className="w-full rounded-2xl border border-line bg-white/90 px-4 py-4 font-mono text-sm leading-7 text-ink shadow-sm outline-none transition focus:border-sage focus:ring-4 focus:ring-sage/10 min-h-[340px]"
                  value={formState.templateContent}
                  onChange={(event) => updateField("templateContent", event.target.value)}
                  required
                />
              </label>

              {errorMessage ? <p className="text-sm text-amber-700">{errorMessage}</p> : null}

              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={closeDialog}>
                  取消
                </Button>
                <Button type="submit" variant="secondary" disabled={isPending}>
                  {isPending ? "提交中..." : editingTemplateId === null ? "创建配置" : "保存修改"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {preview ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-5xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">模板预览</h3>
                <p className="mt-2 text-sm text-slate-600">{preview.templateName}</p>
              </div>
              <Button variant="outline" onClick={() => setPreview(null)}>
                关闭
              </Button>
            </div>

            <div className="mt-6 grid gap-5 lg:grid-cols-2">
              <PreviewBlock title="基础模板正文" value={preview.templateContent} />
              <PreviewBlock title="开关插入片段" value={preview.switchModules || "当前没有打开的开关片段。"} />
              <div className="lg:col-span-2">
                <PreviewBlock title="最终实际调用提示词" value={preview.finalPrompt} />
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}


function PreviewBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white/75 p-4">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap font-mono text-sm leading-7 text-ink">{value}</p>
    </div>
  );
}
