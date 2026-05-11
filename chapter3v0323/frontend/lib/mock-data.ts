export type MetricCard = {
  title: string;
  value: string;
  description: string;
};

export type ModelItem = {
  id: number;
  name: string;
  provider: string;
  apiKey: string;
  baseUrl: string;
  modelName: string;
  isDefault: boolean;
};

export type ModelConfigItem = {
  id: number;
  modelName: string;
  modelCode: string;
  apiUrl: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
  status: number;
  createdTime: string;
  updatedTime: string;
};

export type PromptTemplateConfigItem = {
  id: number;
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
  createdTime: string;
  updatedTime: string;
};

export type DatasetItem = {
  id: number;
  name: string;
  source: string;
  samples: number;
  labeledSamples: number;
  axiomTypes: string[];
  status: "ready" | "processing";
  updatedAt: string;
};

export const dashboardMetrics: MetricCard[] = [
  { title: "已配置模型", value: "11", description: "支持多种大语言模型接入" },
  { title: "已导入数据集", value: "4", description: "DBpedia、NELL、YAGO、Hard Case" },
  { title: "评测任务数", value: "38", description: "包含历史实验与原型任务" },
  { title: "解释标注数", value: "880", description: "正确 / 错误 / 幻觉" },
];

export const recentEvaluations = [
  {
    id: "EV-20260407-001",
    model: "Claude Sonnet 4.6",
    dataset: "Hard Case",
    template: "上下文引导型",
    status: "已完成",
    accuracy: "0.768",
  },
  {
    id: "EV-20260407-002",
    model: "Qwen Max",
    dataset: "Hard Case Stability",
    template: "上下文引导型",
    status: "已完成",
    accuracy: "0.792",
  },
  {
    id: "EV-20260407-003",
    model: "GPT-5.4",
    dataset: "DBpedia",
    template: "指令增强型",
    status: "运行中",
    accuracy: "--",
  },
];

export const models: ModelItem[] = [
  { id: 1, name: "Claude Sonnet 4.6", provider: "Anthropic", apiKey: "sk-demo-anthropic", baseUrl: "https://api2.aigcbest.top/v1", modelName: "claude-sonnet-4-6", isDefault: false },
  { id: 2, name: "Claude Haiku 4.5", provider: "Anthropic", apiKey: "sk-demo-anthropic", baseUrl: "https://api2.aigcbest.top/v1", modelName: "claude-haiku-4-5-20251001", isDefault: false },
  { id: 3, name: "GPT-5.4", provider: "OpenAI", apiKey: "sk-demo-openai", baseUrl: "https://api2.aigcbest.top/v1", modelName: "gpt-5.4", isDefault: true },
  { id: 4, name: "GPT-5 Mini", provider: "OpenAI", apiKey: "sk-demo-openai", baseUrl: "https://api2.aigcbest.top/v1", modelName: "gpt-5-mini", isDefault: false },
  { id: 5, name: "Qwen Max", provider: "Alibaba", apiKey: "sk-demo-alibaba", baseUrl: "https://api2.aigcbest.top/v1", modelName: "qwen-max-0125", isDefault: false },
];

export const modelConfigs: ModelConfigItem[] = [
  {
    id: 1,
    modelName: "Claude Sonnet 4.6",
    modelCode: "claude-sonnet-4-6",
    apiUrl: "https://api2.aigcbest.top/v1",
    apiKey: "sk-demo-claude",
    temperature: 0.2,
    maxTokens: 4096,
    status: 1,
    createdTime: "2026-04-21 09:00:00",
    updatedTime: "2026-04-21 09:00:00",
  },
  {
    id: 2,
    modelName: "GPT-5.4",
    modelCode: "gpt-5.4",
    apiUrl: "https://api2.aigcbest.top/v1",
    apiKey: "sk-demo-openai",
    temperature: 0.1,
    maxTokens: 4096,
    status: 1,
    createdTime: "2026-04-21 09:05:00",
    updatedTime: "2026-04-21 09:05:00",
  },
];

export const datasets: DatasetItem[] = [
  { id: 1, name: "DBpedia RDFS Eval", source: "DBpedia", samples: 760, labeledSamples: 760, axiomTypes: ["domain", "range", "subClassOf", "subPropertyOf"], status: "ready", updatedAt: "2026-03-28 16:10" },
  { id: 2, name: "NELL RDFS Eval", source: "NELL", samples: 480, labeledSamples: 480, axiomTypes: ["domain", "range", "subClassOf", "subPropertyOf"], status: "ready", updatedAt: "2026-03-29 10:22" },
  { id: 3, name: "YAGO RDFS Eval", source: "YAGO", samples: 480, labeledSamples: 480, axiomTypes: ["domain", "range", "subClassOf", "subPropertyOf"], status: "ready", updatedAt: "2026-03-29 15:36" },
  { id: 4, name: "Hard Case 数据集", source: "人工构造", samples: 431, labeledSamples: 431, axiomTypes: ["domain", "range", "subClassOf", "subPropertyOf"], status: "ready", updatedAt: "2026-04-01 09:02" },
];

export const datasetPreviewRows = [
  {
    sampleId: "hard_case_0001",
    axiomType: "subClassOf",
    axiomText: "Airline ⊑ PublicTransitSystem",
    label: "错误",
    source: "hard_case",
  },
  {
    sampleId: "hard_case_0002",
    axiomType: "subClassOf",
    axiomText: "Album ⊑ MusicalWork",
    label: "正确",
    source: "hard_case",
  },
  {
    sampleId: "hard_case_0103",
    axiomType: "domain",
    axiomText: "birthPlace domain Person",
    label: "正确",
    source: "hard_case",
  },
  {
    sampleId: "hard_case_0217",
    axiomType: "range",
    axiomText: "spouse range Person",
    label: "正确",
    source: "hard_case",
  },
];

export const promptTemplates = [
  {
    name: "基础型提示词",
    type: "基础型",
    summary: "使用最简洁的判断格式，适合快速基线实验。",
  },
  {
    name: "指令增强型提示词",
    type: "指令增强型",
    summary: "强调显式推理步骤，提高结构化判断质量。",
  },
  {
    name: "上下文引导型提示词",
    type: "上下文引导型",
    summary: "结合背景知识、RDFS 语义规则和常识进行判断。",
  },
];

export const promptTemplateConfigs: PromptTemplateConfigItem[] = [
  {
    id: 1,
    templateName: "语义网络层提示词",
    taskType: "ontology_learning",
    templateType: "meaning",
    layerName: "meaning",
    templateContent: "请从论文文本中抽取语义关系，输出结构化 JSON。",
    switchCount: 1,
    switchDomain: 1,
    switchNaming: 1,
    switchEntity: 0,
    remark: "第一层语义关系抽取模板",
    status: 1,
    createdTime: "2026-04-21 10:00:00",
    updatedTime: "2026-04-21 10:00:00",
  },
  {
    id: 2,
    templateName: "术语归并层提示词",
    taskType: "ontology_learning",
    templateType: "term",
    layerName: "term",
    templateContent: "请对上一层结果进行术语归并和命名规范化。",
    switchCount: 1,
    switchDomain: 1,
    switchNaming: 1,
    switchEntity: 1,
    remark: "第二层术语规范化模板",
    status: 1,
    createdTime: "2026-04-21 10:05:00",
    updatedTime: "2026-04-21 10:05:00",
  },
];

export type EvaluationJobItem = {
  id: string;
  name: string;
  model: string;
  dataset: string;
  template: string;
  status: "已完成" | "运行中" | "排队中";
  createdAt: string;
  samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};

export type EvaluationResultRow = {
  sampleId: string;
  axiomType: string;
  axiomText: string;
  judgment: "正确" | "错误";
  explanation: string;
  responseTime: string;
  tokens: number;
};

export type AnnotationItem = {
  model: string;
  sampleId: string;
  axiomType: string;
  axiomText: string;
  contextInfo: string;
  modelOutput: string;
  explanationText: string;
  label: "correct" | "wrong" | "hallucination" | "pending";
};

export type StabilityVariant = {
  variant: string;
  expression: string;
  result: "正确" | "错误";
};

export const evaluationJobs: EvaluationJobItem[] = [
  {
    id: "EV-20260407-001",
    name: "Hard Case / Claude Sonnet 4.6 / 上下文引导型",
    model: "Claude Sonnet 4.6",
    dataset: "Hard Case 数据集",
    template: "上下文引导型",
    status: "已完成",
    createdAt: "2026-04-07 09:20",
    samples: 431,
    accuracy: 0.768,
    precision: 0.821,
    recall: 0.734,
    f1: 0.775,
  },
  {
    id: "EV-20260407-002",
    name: "Hard Case Stability / Qwen Max / 上下文引导型",
    model: "Qwen Max",
    dataset: "Hard Case Stability 数据集",
    template: "上下文引导型",
    status: "已完成",
    createdAt: "2026-04-07 09:48",
    samples: 431,
    accuracy: 0.792,
    precision: 0.845,
    recall: 0.761,
    f1: 0.801,
  },
  {
    id: "EV-20260407-003",
    name: "DBpedia / GPT-5.4 / 指令增强型",
    model: "GPT-5.4",
    dataset: "DBpedia RDFS Eval",
    template: "指令增强型",
    status: "运行中",
    createdAt: "2026-04-07 10:05",
    samples: 760,
    accuracy: 0.0,
    precision: 0.0,
    recall: 0.0,
    f1: 0.0,
  },
];

export const evaluationTypeMetrics = [
  { axiomType: "domain", accuracy: 0.73, f1: 0.75 },
  { axiomType: "range", accuracy: 0.81, f1: 0.82 },
  { axiomType: "subClassOf", accuracy: 0.78, f1: 0.77 },
  { axiomType: "subPropertyOf", accuracy: 0.75, f1: 0.76 },
];

export const evaluationResultRows: EvaluationResultRow[] = [
  {
    sampleId: "hard_case_0002",
    axiomType: "subClassOf",
    axiomText: "Album ⊑ MusicalWork",
    judgment: "正确",
    explanation: "Album 表示音乐作品的一个子类，与 MusicalWork 的语义包含关系一致。",
    responseTime: "1.28s",
    tokens: 486,
  },
  {
    sampleId: "hard_case_0103",
    axiomType: "domain",
    axiomText: "birthPlace domain Person",
    judgment: "正确",
    explanation: "birthPlace 的主语通常是拥有出生地的实体，因此 domain 约束为 Person 合理。",
    responseTime: "1.06s",
    tokens: 438,
  },
  {
    sampleId: "hard_case_0217",
    axiomType: "range",
    axiomText: "spouse range Person",
    judgment: "正确",
    explanation: "spouse 的客体语义上对应配偶实体，通常属于 Person 类。",
    responseTime: "1.12s",
    tokens: 451,
  },
  {
    sampleId: "hard_case_0321",
    axiomType: "subPropertyOf",
    axiomText: "doctoralAdvisor ⊑ advisor",
    judgment: "正确",
    explanation: "doctoralAdvisor 是 advisor 的更具体关系，符合子属性语义。",
    responseTime: "1.34s",
    tokens: 503,
  },
];

export const annotationItems: AnnotationItem[] = [
  {
    model: "Claude Sonnet 4.6",
    sampleId: "ann_0001",
    axiomType: "domain",
    axiomText: "birthPlace domain Person",
    contextInfo: "Person 表示人类个体；birthPlace 描述一个实体的出生地点。",
    modelOutput: "判断结果：[正确]\n解释：[birthPlace 的主体通常是人，因此 domain 为 Person 合理。]",
    explanationText: "birthPlace 的主体通常是人，因此 domain 为 Person 合理。",
    label: "correct",
  },
  {
    model: "Qwen Max",
    sampleId: "ann_0002",
    axiomType: "subClassOf",
    axiomText: "Airline ⊑ PublicTransitSystem",
    contextInfo: "Airline 是航空公司；PublicTransitSystem 通常指公共交通系统。",
    modelOutput: "判断结果：[错误]\n解释：[航空公司是运营主体，不是公共交通系统本身。]",
    explanationText: "航空公司是运营主体，不是公共交通系统本身。",
    label: "correct",
  },
  {
    model: "GPT-5 Mini",
    sampleId: "ann_0003",
    axiomType: "range",
    axiomText: "spouse range Person",
    contextInfo: "spouse 表示配偶关系。",
    modelOutput: "判断结果：[正确]\n解释：[因为 spouse 在很多知识图谱里也可以连接地点，所以该说明存在泛化。]",
    explanationText: "因为 spouse 在很多知识图谱里也可以连接地点，所以该说明存在泛化。",
    label: "hallucination",
  },
];

export const annotationSummary = [
  { label: "correct", count: 512 },
  { label: "wrong", count: 178 },
  { label: "hallucination", count: 190 },
];

export const stabilityCase = {
  model: "Qwen Max",
  hardConsistency: 0.60,
  softConsistency: 0.07,
  original: "doctoralAdvisor ⊑ advisor",
  variants: [
    {
      variant: "Original",
      expression: "doctoralAdvisor ⊑ advisor",
      result: "正确",
    },
    {
      variant: "Variant 1",
      expression: "doctoralAdvisor is a subPropertyOf advisor",
      result: "正确",
    },
    {
      variant: "Variant 2",
      expression: "If x has a doctoral advisor y, then x also has an advisor y",
      result: "正确",
    },
    {
      variant: "Variant 3",
      expression: "doctoralAdvisor can be viewed as a specialized form of advisor",
      result: "错误",
    },
    {
      variant: "Variant 4",
      expression: "advisor subsumes doctoralAdvisor in semantic scope",
      result: "正确",
    },
    {
      variant: "Variant 5",
      expression: "Any doctoralAdvisor relation should imply the more general advisor relation",
      result: "错误",
    },
  ] as StabilityVariant[],
};

export const stabilityLeaderboard = [
  { model: "Claude Sonnet 4.6", hard: 0.63, soft: 0.06 },
  { model: "Qwen Max", hard: 0.60, soft: 0.07 },
  { model: "GPT-5.4", hard: 0.59, soft: 0.08 },
  { model: "Gemini 2.5 Pro", hard: 0.57, soft: 0.09 },
  { model: "DeepSeek R1", hard: 0.52, soft: 0.10 },
];

export const ontologyNodes = [
  { id: "Person", x: "18%", y: "26%", type: "Class" },
  { id: "Place", x: "79%", y: "26%", type: "Class" },
  { id: "birthPlace", x: "48%", y: "18%", type: "Property" },
  { id: "MusicalWork", x: "24%", y: "72%", type: "Class" },
  { id: "Album", x: "46%", y: "62%", type: "Class" },
  { id: "advisor", x: "72%", y: "68%", type: "Property" },
  { id: "doctoralAdvisor", x: "76%", y: "84%", type: "Property" },
];

export const ontologyEdges = [
  { from: "birthPlace", to: "Person", label: "domain" },
  { from: "birthPlace", to: "Place", label: "range" },
  { from: "Album", to: "MusicalWork", label: "subClassOf" },
  { from: "doctoralAdvisor", to: "advisor", label: "subPropertyOf" },
];

export const ontologyDetails = [
  { key: "当前节点", value: "Album" },
  { key: "节点类型", value: "类" },
  { key: "关联公理", value: "subClassOf MusicalWork" },
  { key: "来源数据集", value: "Hard Case / DBpedia" },
];

export const exportOptions = [
  {
    title: "评测结果导出",
    description: "导出任务级指标统计与样本级判断结果。",
    formats: ["CSV", "JSON"],
    count: "38 组结果",
  },
  {
    title: "解释标注导出",
    description: "下载人工标注后的解释质量记录。",
    formats: ["CSV", "JSON"],
    count: "880 条标注",
  },
  {
    title: "本体数据导出",
    description: "生成用于附录展示和后续处理的本体结构文件。",
    formats: ["Turtle", "RDF/XML", "JSON"],
    count: "4 个数据集",
  },
];

export const exportHistory = [
  {
    id: "EXP-20260407-001",
    resource: "评测结果导出",
    format: "CSV",
    createdAt: "2026-04-07 11:20",
    status: "已就绪",
  },
  {
    id: "EXP-20260407-002",
    resource: "解释标注导出",
    format: "JSON",
    createdAt: "2026-04-07 11:24",
    status: "已就绪",
  },
  {
    id: "EXP-20260407-003",
    resource: "本体数据导出",
    format: "Turtle",
    createdAt: "2026-04-07 11:31",
    status: "生成中",
  },
];
