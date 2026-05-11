import {
  datasets,
  evaluationJobs,
  evaluationResultRows,
  evaluationTypeMetrics,
  modelConfigs,
  models,
  promptTemplateConfigs,
  promptTemplates,
  type EvaluationResultRow,
  type ModelConfigItem,
  type ModelItem,
  type PromptTemplateConfigItem,
} from "@/lib/mock-data";


type ModelApiResponse = {
  id: number;
  name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model_name: string;
  is_default: boolean;
};

type ModelConfigApiResponse = {
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

type DatasetApiResponse = {
  id: number;
  name: string;
  description: string | null;
  source: string | null;
  file_name: string | null;
  row_count: number;
  status: "draft" | "ready" | "processing" | "failed";
  has_labels: boolean;
  created_at: string;
  updated_at: string;
};

type DatasetPreviewApiResponse = {
  id: number;
  dataset_id: number;
  sample_id: string;
  axiom_type: string;
  axiom_text: string;
  subject: string | null;
  predicate: string | null;
  object: string | null;
  label: number | null;
  source: string | null;
  context_info: string | null;
};

type ApiEnvelope<T> = {
  code: number;
  message: string;
  data: T;
};

type EvalDatasetApiResponse = {
  id: number;
  datasetName: string;
  fileName: string;
  recordCount: number;
  remark: string | null;
  createdTime: string;
  updatedTime: string;
};

type EvalDatasetRecordApiResponse = {
  id: number;
  datasetId: number;
  axiomType: string;
  subject: string;
  predicate: string;
  object: string;
  label: number;
  source: string;
  axiomText: string;
  negativeStrategy: string | null;
  subjectContext: string | null;
  objectContext: string | null;
  contextInfo: string | null;
  contextSummary: string | null;
  createdTime: string;
  updatedTime: string;
};

type EvalDatasetUploadApiResponse = {
  dataset: EvalDatasetApiResponse;
  totalCount: number;
  successCount: number;
  failedCount: number;
  errors: string[];
};

type EvalDatasetRecordPageApiResponse = {
  records: EvalDatasetRecordApiResponse[];
  total: number;
  page: number;
  pageSize: number;
};

type EvalTaskApiResponse = {
  id: number;
  taskName: string;
  datasetId: number | null;
  modelId: number | null;
  promptId: number | null;
  taskStatus: string;
  totalCount: number;
  successCount: number;
  failCount: number;
  remark: string | null;
  createdTime: string;
  updatedTime: string;
  datasetName: string | null;
  modelName: string | null;
  promptName: string | null;
};

type EvalTaskDetailApiResponse = {
  task: EvalTaskApiResponse;
  dataset: { id: number; datasetName: string; recordCount: number; fileName: string } | null;
  model: { id: number; modelName: string; modelCode: string } | null;
  prompt: { id: number; templateName: string; templateType: string } | null;
  metrics: EvalTaskMetricsApiResponse;
};

type EvalTaskMetricsApiResponse = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  evaluatedCount: number;
};

type EvalTaskResultApiResponse = {
  id: number;
  taskId: number | null;
  datasetRecordId: number | null;
  axiomType: string | null;
  axiomText: string | null;
  trueLabel: number | null;
  predictLabel: number | null;
  judgmentResult: string | null;
  explanation: string | null;
  rawOutput: string | null;
  runStatus: string;
  errorMessage: string | null;
  createdTime: string;
  updatedTime: string;
};

type EvalTaskResultPageApiResponse = {
  records: EvalTaskResultApiResponse[];
  total: number;
  page: number;
  pageSize: number;
};

type ExplanationEvalAnnotationApiResponse = {
  id: number | null;
  taskId: number;
  resultId: number;
  explanationCorrectLabel: number | null;
  hallucinationLabel: number | null;
  annotationStatus: string;
  annotationRemark: string | null;
  createdTime: string | null;
  updatedTime: string | null;
};

type ExplanationEvalItemApiResponse = {
  resultId: number;
  taskId: number;
  axiomType: string | null;
  axiomText: string | null;
  trueLabel: number | null;
  predictLabel: number | null;
  judgmentResult: string | null;
  explanation: string | null;
  rawOutput: string | null;
  runStatus: string;
  annotation: ExplanationEvalAnnotationApiResponse;
};

type ExplanationEvalPageApiResponse = {
  records: ExplanationEvalItemApiResponse[];
  total: number;
  page: number;
  pageSize: number;
};

type ExplanationEvalStatsApiResponse = {
  correctCaseCount: number;
  annotatedCount: number;
  explanationCorrectCount: number;
  hallucinationCount: number;
  explanationAccuracy: number;
  hallucinationRate: number;
};

type StabilityEvalTaskApiResponse = {
  id: number;
  baseTaskId: number;
  axiomTypeScope: string;
  templateCount: number;
  taskStatus: string;
  totalCount: number;
  successCount: number;
  failCount: number;
  hardConsistency: number | null;
  softConsistency: number | null;
  remark: string | null;
  createdTime: string;
  updatedTime: string;
};

type StabilityEvalRecordApiResponse = {
  id: number;
  stabilityTaskId: number;
  baseTaskId: number;
  resultId: number;
  originalId: string;
  templateId: number;
  variantId: string;
  axiomType: string;
  originalText: string | null;
  perturbedText: string;
  contextInfo: string | null;
  label: number | null;
  originalPredictLabel: number | null;
  perturbedPredictLabel: number | null;
  consistencyFlag: number | null;
  runStatus: string;
  errorMessage: string | null;
  createdTime: string;
  updatedTime: string;
};

type StabilityEvalRecordPageApiResponse = {
  records: StabilityEvalRecordApiResponse[];
  total: number;
  page: number;
  pageSize: number;
};

type OntologyTaskApiResponse = {
  id: number;
  taskName: string;
  taskType: string;
  executionMode: string | null;
  modelId: number;
  promptId: number;
  semanticPromptId: number | null;
  termPromptId: number | null;
  conceptPromptId: number | null;
  domainType: string;
  domainSwitch: number;
  chunkMetadataSwitch: number;
  inputType: string | null;
  fileName: string | null;
  filePath: string | null;
  totalChunkCount: number;
  successCount: number;
  failCount: number;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntityDefinition: number;
  inputText: string | null;
  finalPrompt: string | null;
  outputContent: string | null;
  mergedOutput: string | null;
  taskStatus: string;
  errorMessage: string | null;
  remark: string | null;
  createdTime: string;
  updatedTime: string;
  modelName: string | null;
  promptName: string | null;
};

type OntologyChunkApiResponse = {
  id: number;
  taskId: number;
  chunkId: string;
  chunkIndex: number;
  sectionTitle: string | null;
  pageStart: number | null;
  pageEnd: number | null;
  chunkText: string;
  createdTime: string;
  updatedTime: string;
  resultId: number | null;
  runStatus: string | null;
  errorMessage: string | null;
  classCount: number;
  propertyCount: number;
  subClassOfCount: number;
  subPropertyOfCount: number;
  domainCount: number;
  rangeCount: number;
  semanticNetworkStatus: string | null;
  termRefinementStatus: string | null;
  conceptModelingStatus: string | null;
};

type OntologyChunkDetailApiResponse = {
  chunk: OntologyChunkApiResponse;
  result: OntologyChunkResultApiResponse | null;
  layerResults?: OntologyChunkResultApiResponse[];
};

type OntologyChunkResultApiResponse = {
    id: number;
    taskId: number;
    chunkRecordId: number;
    executionMode: string;
    layerName: string | null;
    finalPrompt: string | null;
    outputContent: string | null;
    parsedOutput: unknown;
    runStatus: string;
    errorMessage: string | null;
    createdTime: string;
    updatedTime: string;
};

type OntologyTaskStatsApiResponse = {
  totalChunkCount: number;
  successCount: number;
  failCount: number;
  classCount: number;
  propertyCount: number;
  subClassOfCount: number;
  subPropertyOfCount: number;
  domainCount: number;
  rangeCount: number;
  semanticNetworkSuccessCount: number;
  termRefinementSuccessCount: number;
  conceptModelingSuccessCount: number;
};

type OntologyResultApiResponse = {
  task: {
    id: number;
    taskName: string;
    executionMode: string | null;
    domainType: string;
    taskStatus: string;
    fileName: string | null;
    totalChunkCount: number;
    successCount: number;
    failCount: number;
    createdTime: string;
    updatedTime: string;
  };
  overview: Record<string, number | string | null>;
  axioms: OntologyAxiomApiResponse[];
  graph: {
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ id: string; source: string; target: string; label: string; type: string }>;
  };
  charts: {
    axiomDistribution: Array<{ name: string; value: number }>;
    classPropertyComparison: Array<{ name: string; value: number }>;
    chunkExecution: Array<{ name: string; value: number }>;
  };
};

type OntologyAxiomApiResponse = {
  id: number;
  taskId: number;
  executionMode: string;
  sourceLayer: string;
  axiomType: string;
  subjectTerm: string | null;
  objectTerm: string | null;
  axiomText: string | null;
  payloadJson: unknown;
  createdTime: string;
  updatedTime: string;
};

type OntologyExportApiResponse = {
  format: string;
  filename: string;
  content: string;
};

type OntologyLayerResultsApiResponse = {
  taskId: number;
  executionMode: string | null;
  layers: Record<string, Array<{
    id: number;
    chunkRecordId: number;
    layerName: string;
    runStatus: string;
    errorMessage: string | null;
    finalPrompt: string | null;
    outputContent: string | null;
    parsedOutput: unknown;
    createdTime: string;
    updatedTime: string;
  }>>;
};

type StabilityTemplateApiResponse = Record<string, Array<{ templateId: number; templateText: string }>>;

type EvalReportApiResponse = {
  taskInfo: {
    id: number;
    taskName: string;
    datasetName: string | null;
    modelName: string | null;
    promptName: string | null;
    createdTime: string;
    taskStatus: string;
  };
  classification: {
    totalCount: number;
    successCount: number;
    failCount: number;
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
  };
  explanation: {
    correctCaseCount: number;
    annotatedCount: number;
    explanationCorrectCount: number;
    hallucinationCount: number;
    explanationAccuracy: number;
    hallucinationRate: number;
  };
  stability: {
    hasData: boolean;
    stabilityTaskId: number | null;
    taskStatus: string;
    totalCount: number;
    successCount: number;
    failCount: number;
    hardConsistency: number;
    softConsistency: number;
  };
  charts: {
    classification: Array<{ name: string; value: number }>;
    explanation: Array<{ name: string; value: number }>;
    stability: Array<{ name: string; value: number }>;
  };
};

type PromptTemplateApiResponse = {
  id: number;
  name: string;
  template_type: "basic" | "instruction_enhanced" | "context_guided";
  content?: string;
  description?: string | null;
  is_default: boolean;
  is_active?: boolean;
};

type PromptTemplateConfigApiResponse = {
  id: number;
  templateName: string;
  taskType: string;
  templateType: string;
    layerName: string | null;
  templateContent: string;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntity: number;
  remark: string | null;
  status: number;
  createdTime: string;
  updatedTime: string;
};

type PromptTemplateConfigPreviewApiResponse = {
  templateId: number;
  templateName: string;
  templateContent: string;
  switchModules: string;
  finalPrompt: string;
};

type EvaluationTaskApiResponse = {
  id: number;
  name: string;
  status: "pending" | "running" | "succeeded" | "failed";
  dataset_id: number;
  model_id: number;
  prompt_template_id: number;
  created_at: string;
};

type EvaluationTaskDetailApiResponse = {
  id: number;
  name: string;
  status: "pending" | "running" | "succeeded" | "failed";
  dataset_id: number;
  model_id: number;
  prompt_template_id: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
};

type EvaluationMetricsApiResponse = {
  overall: {
    total: number;
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
  };
  by_axiom_type: Record<
    string,
    {
      total: number;
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
    }
  >;
};

type EvaluationResultApiResponse = {
  id: number;
  sample_id: string | null;
  axiom_type: string | null;
  axiom_text: string | null;
  judgment_result: string | null;
  explanation: string | null;
  raw_response: string | null;
  response_time_ms: number | null;
  total_tokens: number | null;
  dataset_record_id: number;
};

type AnnotationResultApiResponse = {
  evaluation_result_id: number;
  sample_id: string | null;
  axiom_type: string | null;
  axiom_text: string | null;
  judgment_result: string | null;
  explanation: string | null;
  raw_response: string | null;
  explanation_label: "correct" | "wrong" | "hallucination" | null;
  annotation_reason: string | null;
};

type AnnotationStatsApiResponse = {
  overall: {
    total_annotations: number;
    correct_count: number;
    hallucination_count: number;
    explanation_accuracy: number;
    hallucination_rate: number;
  };
  by_model: Record<
    string,
    {
      total_annotations: number;
      correct_count: number;
      hallucination_count: number;
      explanation_accuracy: number;
      hallucination_rate: number;
    }
  >;
};

export type EvaluationListItem = {
  id: string;
  name: string;
  model: string;
  dataset: string;
  template: string;
  status: "已完成" | "运行中" | "排队中" | "失败";
  createdAt: string;
  samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};

export type EvaluationDetailData = {
  id: string;
  name: string;
  model: string;
  dataset: string;
  template: string;
  status: "已完成" | "运行中" | "排队中" | "失败";
  samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  typeMetrics: Array<{
    axiomType: string;
    total: number;
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
  }>;
  results: EvaluationResultRow[];
};

export type EvaluationCreateOptions = {
  models: ModelItem[];
  datasets: DatasetListItem[];
  templates: PromptTemplateItem[];
};

export type EvaluationCreateResult = {
  taskId: number;
  taskName: string;
  status: string;
  resultCount: number;
};

export type AnnotationItemData = {
  evaluationResultId: number;
  sampleId: string;
  axiomType: string;
  axiomText: string;
  judgmentResult: string;
  explanation: string;
  rawResponse: string;
  explanationLabel: "correct" | "wrong" | "hallucination" | null;
  annotationReason: string;
};

export type ExplanationStatsData = {
  overall: {
    totalAnnotations: number;
    correctCount: number;
    hallucinationCount: number;
    explanationAccuracy: number;
    hallucinationRate: number;
  };
  byModel: Array<{
    model: string;
    totalAnnotations: number;
    correctCount: number;
    hallucinationCount: number;
    explanationAccuracy: number;
    hallucinationRate: number;
  }>;
};

export type DashboardStatsData = {
  modelCount: number;
  datasetCount: number;
  evaluationCount: number;
  annotationCount: number;
};

export type DatasetListItem = {
  id: number;
  name: string;
  source: string;
  samples: number;
  labeledSamples: number;
  status: "ready" | "processing";
  updatedAt: string;
  fileName: string | null;
};

export type DatasetPreviewRow = {
  sampleId: string;
  axiomType: string;
  axiomText: string;
  label: string;
  source: string;
};

export type DatasetDetailData = {
  id: number;
  name: string;
  description: string;
  source: string;
  samples: number;
  labeledSamples: number;
  status: "ready" | "processing";
  fileName: string | null;
  previewRows: DatasetPreviewRow[];
};

export type EvalDatasetListItem = {
  id: number;
  datasetName: string;
  fileName: string;
  recordCount: number;
  remark: string;
  createdTime: string;
  updatedTime: string;
};

export type EvalDatasetRecordItem = {
  id: number;
  datasetId: number;
  axiomType: string;
  subject: string;
  predicate: string;
  object: string;
  label: number;
  source: string;
  axiomText: string;
  negativeStrategy: string;
  subjectContext: string;
  objectContext: string;
  contextInfo: string;
  contextSummary: string;
  createdTime: string;
  updatedTime: string;
};

export type EvalDatasetUploadResult = {
  dataset: EvalDatasetListItem;
  totalCount: number;
  successCount: number;
  failedCount: number;
  errors: string[];
};

export type EvalDatasetRecordPage = {
  records: EvalDatasetRecordItem[];
  total: number;
  page: number;
  pageSize: number;
};

export type EvalTaskItem = {
  id: number;
  taskName: string;
  datasetId: number | null;
  modelId: number | null;
  promptId: number | null;
  taskStatus: string;
  totalCount: number;
  successCount: number;
  failCount: number;
  remark: string;
  createdTime: string;
  updatedTime: string;
  datasetName: string;
  modelName: string;
  promptName: string;
};

export type EvalTaskPayload = {
  taskName: string;
  datasetId: number;
  modelId: number;
  promptId: number;
  remark: string | null;
};

export type EvalTaskMetrics = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  evaluatedCount: number;
};

export type EvalTaskDetail = {
  task: EvalTaskItem;
  dataset: { id: number; datasetName: string; recordCount: number; fileName: string } | null;
  model: { id: number; modelName: string; modelCode: string } | null;
  prompt: { id: number; templateName: string; templateType: string } | null;
  metrics: EvalTaskMetrics;
};

export type EvalTaskResultItem = {
  id: number;
  taskId: number | null;
  datasetRecordId: number | null;
  axiomType: string;
  axiomText: string;
  trueLabel: number | null;
  predictLabel: number | null;
  judgmentResult: string;
  explanation: string;
  rawOutput: string;
  runStatus: string;
  errorMessage: string;
  createdTime: string;
  updatedTime: string;
};

export type EvalTaskResultPage = {
  records: EvalTaskResultItem[];
  total: number;
  page: number;
  pageSize: number;
};

export type ExplanationEvalAnnotation = {
  id: number | null;
  taskId: number;
  resultId: number;
  explanationCorrectLabel: number | null;
  hallucinationLabel: number | null;
  annotationStatus: string;
  annotationRemark: string;
  createdTime: string;
  updatedTime: string;
};

export type ExplanationEvalItem = {
  resultId: number;
  taskId: number;
  axiomType: string;
  axiomText: string;
  trueLabel: number | null;
  predictLabel: number | null;
  judgmentResult: string;
  explanation: string;
  rawOutput: string;
  runStatus: string;
  annotation: ExplanationEvalAnnotation;
};

export type ExplanationEvalPage = {
  records: ExplanationEvalItem[];
  total: number;
  page: number;
  pageSize: number;
};

export type ExplanationEvalStats = {
  correctCaseCount: number;
  annotatedCount: number;
  explanationCorrectCount: number;
  hallucinationCount: number;
  explanationAccuracy: number;
  hallucinationRate: number;
};

export type ExplanationEvalPayload = {
  taskId: number;
  resultId: number;
  explanationCorrectLabel: number | null;
  hallucinationLabel: number | null;
  annotationRemark: string | null;
};

export type StabilityEvalTaskItem = {
  id: number;
  baseTaskId: number;
  axiomTypeScope: string;
  templateCount: number;
  taskStatus: string;
  totalCount: number;
  successCount: number;
  failCount: number;
  hardConsistency: number | null;
  softConsistency: number | null;
  remark: string;
  createdTime: string;
  updatedTime: string;
};

export type StabilityEvalRecordItem = {
  id: number;
  stabilityTaskId: number;
  baseTaskId: number;
  resultId: number;
  originalId: string;
  templateId: number;
  variantId: string;
  axiomType: string;
  originalText: string;
  perturbedText: string;
  contextInfo: string;
  label: number | null;
  originalPredictLabel: number | null;
  perturbedPredictLabel: number | null;
  consistencyFlag: number | null;
  runStatus: string;
  errorMessage: string;
  createdTime: string;
  updatedTime: string;
};

export type StabilityEvalRecordPage = {
  records: StabilityEvalRecordItem[];
  total: number;
  page: number;
  pageSize: number;
};

export type StabilityTemplateMap = Record<string, Array<{ templateId: number; templateText: string }>>;

export type EvalReportData = {
  taskInfo: {
    id: number;
    taskName: string;
    datasetName: string;
    modelName: string;
    promptName: string;
    createdTime: string;
    taskStatus: string;
  };
  classification: EvalReportApiResponse["classification"];
  explanation: EvalReportApiResponse["explanation"];
  stability: EvalReportApiResponse["stability"];
  charts: EvalReportApiResponse["charts"];
};

export type PromptTemplateConfigPreview = {
  templateId: number;
  templateName: string;
  templateContent: string;
  switchModules: string;
  finalPrompt: string;
};

export type PromptTemplateItem = {
  id: number;
  name: string;
  templateType: "basic" | "instruction_enhanced" | "context_guided";
  content: string;
  description: string;
  isDefault: boolean;
};


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";


function mapModel(model: ModelApiResponse): ModelItem {
  return {
    id: model.id,
    name: model.name,
    provider: model.provider,
    apiKey: model.api_key,
    baseUrl: model.base_url,
    modelName: model.model_name,
    isDefault: model.is_default,
  };
}


function mapModelConfig(config: ModelConfigApiResponse): ModelConfigItem {
  return {
    id: config.id,
    modelName: config.modelName,
    modelCode: config.modelCode,
    apiUrl: config.apiUrl,
    apiKey: config.apiKey,
    temperature: Number(config.temperature),
    maxTokens: config.maxTokens,
    status: config.status,
    createdTime: formatTimestamp(config.createdTime),
    updatedTime: formatTimestamp(config.updatedTime),
  };
}


function mapEvalDataset(dataset: EvalDatasetApiResponse): EvalDatasetListItem {
  return {
    id: dataset.id,
    datasetName: dataset.datasetName,
    fileName: dataset.fileName,
    recordCount: dataset.recordCount,
    remark: dataset.remark ?? "",
    createdTime: formatTimestamp(dataset.createdTime),
    updatedTime: formatTimestamp(dataset.updatedTime),
  };
}


function mapEvalDatasetRecord(record: EvalDatasetRecordApiResponse): EvalDatasetRecordItem {
  return {
    id: record.id,
    datasetId: record.datasetId,
    axiomType: record.axiomType,
    subject: record.subject,
    predicate: record.predicate,
    object: record.object,
    label: record.label,
    source: record.source,
    axiomText: record.axiomText,
    negativeStrategy: record.negativeStrategy ?? "",
    subjectContext: record.subjectContext ?? "",
    objectContext: record.objectContext ?? "",
    contextInfo: record.contextInfo ?? "",
    contextSummary: record.contextSummary ?? "",
    createdTime: formatTimestamp(record.createdTime),
    updatedTime: formatTimestamp(record.updatedTime),
  };
}

function mapEvalTask(task: EvalTaskApiResponse): EvalTaskItem {
  return {
    id: task.id,
    taskName: task.taskName,
    datasetId: task.datasetId,
    modelId: task.modelId,
    promptId: task.promptId,
    taskStatus: task.taskStatus,
    totalCount: task.totalCount,
    successCount: task.successCount,
    failCount: task.failCount,
    remark: task.remark ?? "",
    createdTime: formatTimestamp(task.createdTime),
    updatedTime: formatTimestamp(task.updatedTime),
    datasetName: task.datasetName ?? "--",
    modelName: task.modelName ?? "--",
    promptName: task.promptName ?? "--",
  };
}


function mapEvalTaskResult(result: EvalTaskResultApiResponse): EvalTaskResultItem {
  return {
    id: result.id,
    taskId: result.taskId,
    datasetRecordId: result.datasetRecordId,
    axiomType: result.axiomType ?? "",
    axiomText: result.axiomText ?? "",
    trueLabel: result.trueLabel,
    predictLabel: result.predictLabel,
    judgmentResult: result.judgmentResult ?? "",
    explanation: result.explanation ?? "",
    rawOutput: result.rawOutput ?? "",
    runStatus: result.runStatus,
    errorMessage: result.errorMessage ?? "",
    createdTime: formatTimestamp(result.createdTime),
    updatedTime: formatTimestamp(result.updatedTime),
  };
}


function mapExplanationEvalItem(item: ExplanationEvalItemApiResponse): ExplanationEvalItem {
  return {
    resultId: item.resultId,
    taskId: item.taskId,
    axiomType: item.axiomType ?? "",
    axiomText: item.axiomText ?? "",
    trueLabel: item.trueLabel,
    predictLabel: item.predictLabel,
    judgmentResult: item.judgmentResult ?? "",
    explanation: item.explanation ?? "",
    rawOutput: item.rawOutput ?? "",
    runStatus: item.runStatus,
    annotation: {
      id: item.annotation.id,
      taskId: item.annotation.taskId,
      resultId: item.annotation.resultId,
      explanationCorrectLabel: item.annotation.explanationCorrectLabel,
      hallucinationLabel: item.annotation.hallucinationLabel,
      annotationStatus: item.annotation.annotationStatus,
      annotationRemark: item.annotation.annotationRemark ?? "",
      createdTime: item.annotation.createdTime ? formatTimestamp(item.annotation.createdTime) : "",
      updatedTime: item.annotation.updatedTime ? formatTimestamp(item.annotation.updatedTime) : "",
    },
  };
}


function mapStabilityEvalTask(task: StabilityEvalTaskApiResponse): StabilityEvalTaskItem {
  return {
    id: task.id,
    baseTaskId: task.baseTaskId,
    axiomTypeScope: task.axiomTypeScope,
    templateCount: task.templateCount,
    taskStatus: task.taskStatus,
    totalCount: task.totalCount,
    successCount: task.successCount,
    failCount: task.failCount,
    hardConsistency: task.hardConsistency,
    softConsistency: task.softConsistency,
    remark: task.remark ?? "",
    createdTime: formatTimestamp(task.createdTime),
    updatedTime: formatTimestamp(task.updatedTime),
  };
}


function mapStabilityEvalRecord(record: StabilityEvalRecordApiResponse): StabilityEvalRecordItem {
  return {
    id: record.id,
    stabilityTaskId: record.stabilityTaskId,
    baseTaskId: record.baseTaskId,
    resultId: record.resultId,
    originalId: record.originalId,
    templateId: record.templateId,
    variantId: record.variantId,
    axiomType: record.axiomType,
    originalText: record.originalText ?? "",
    perturbedText: record.perturbedText,
    contextInfo: record.contextInfo ?? "",
    label: record.label,
    originalPredictLabel: record.originalPredictLabel,
    perturbedPredictLabel: record.perturbedPredictLabel,
    consistencyFlag: record.consistencyFlag,
    runStatus: record.runStatus,
    errorMessage: record.errorMessage ?? "",
    createdTime: formatTimestamp(record.createdTime),
    updatedTime: formatTimestamp(record.updatedTime),
  };
}


function mapEvalReport(report: EvalReportApiResponse): EvalReportData {
  return {
    taskInfo: {
      id: report.taskInfo.id,
      taskName: report.taskInfo.taskName,
      datasetName: report.taskInfo.datasetName ?? "--",
      modelName: report.taskInfo.modelName ?? "--",
      promptName: report.taskInfo.promptName ?? "--",
      createdTime: formatTimestamp(report.taskInfo.createdTime),
      taskStatus: report.taskInfo.taskStatus,
    },
    classification: report.classification,
    explanation: report.explanation,
    stability: report.stability,
    charts: report.charts,
  };
}

function mapPromptTemplateConfig(config: PromptTemplateConfigApiResponse): PromptTemplateConfigItem {
  return {
    id: config.id,
    templateName: config.templateName,
    taskType: config.taskType,
    templateType: config.templateType,
    layerName: config.layerName ?? "",
    templateContent: config.templateContent,
    switchCount: config.switchCount,
    switchDomain: config.switchDomain,
    switchNaming: config.switchNaming,
    switchEntity: config.switchEntity,
    remark: config.remark ?? "",
    status: config.status,
    createdTime: formatTimestamp(config.createdTime),
    updatedTime: formatTimestamp(config.updatedTime),
  };
}


function mapOntologyTask(task: OntologyTaskApiResponse): OntologyTaskItem {
  return {
    id: task.id,
    taskName: task.taskName,
    taskType: task.taskType,
    executionMode: task.executionMode ?? "",
    modelId: task.modelId,
    promptId: task.promptId,
    semanticPromptId: task.semanticPromptId,
    termPromptId: task.termPromptId,
    conceptPromptId: task.conceptPromptId,
    domainType: task.domainType,
    domainSwitch: task.domainSwitch,
    chunkMetadataSwitch: task.chunkMetadataSwitch,
    inputType: task.inputType ?? "",
    fileName: task.fileName ?? "",
    filePath: task.filePath ?? "",
    totalChunkCount: task.totalChunkCount,
    successCount: task.successCount,
    failCount: task.failCount,
    switchCount: task.switchCount,
    switchDomain: task.switchDomain,
    switchNaming: task.switchNaming,
    switchEntityDefinition: task.switchEntityDefinition,
    inputText: task.inputText ?? "",
    finalPrompt: task.finalPrompt ?? "",
    outputContent: task.outputContent ?? "",
    mergedOutput: task.mergedOutput ?? "",
    taskStatus: task.taskStatus,
    errorMessage: task.errorMessage ?? "",
    remark: task.remark ?? "",
    createdTime: formatTimestamp(task.createdTime),
    updatedTime: formatTimestamp(task.updatedTime),
    modelName: task.modelName ?? "--",
    promptName: task.promptName ?? "--",
  };
}


function mapOntologyChunk(chunk: OntologyChunkApiResponse): OntologyChunkItem {
  return {
    id: chunk.id,
    taskId: chunk.taskId,
    chunkId: chunk.chunkId,
    chunkIndex: chunk.chunkIndex,
    sectionTitle: chunk.sectionTitle ?? "",
    pageStart: chunk.pageStart,
    pageEnd: chunk.pageEnd,
    chunkText: chunk.chunkText,
    createdTime: formatTimestamp(chunk.createdTime),
    updatedTime: formatTimestamp(chunk.updatedTime),
    resultId: chunk.resultId,
    runStatus: chunk.runStatus ?? "pending",
    errorMessage: chunk.errorMessage ?? "",
    classCount: chunk.classCount,
    propertyCount: chunk.propertyCount,
    subClassOfCount: chunk.subClassOfCount,
    subPropertyOfCount: chunk.subPropertyOfCount,
    domainCount: chunk.domainCount,
    rangeCount: chunk.rangeCount,
    semanticNetworkStatus: chunk.semanticNetworkStatus ?? "",
    termRefinementStatus: chunk.termRefinementStatus ?? "",
    conceptModelingStatus: chunk.conceptModelingStatus ?? "",
  };
}


function mapOntologyChunkResult(result: OntologyChunkResultApiResponse): OntologyChunkResultItem {
  return {
    id: result.id,
    taskId: result.taskId,
    chunkRecordId: result.chunkRecordId,
    executionMode: result.executionMode,
    layerName: result.layerName ?? "",
    finalPrompt: result.finalPrompt ?? "",
    outputContent: result.outputContent ?? "",
    parsedOutput: result.parsedOutput,
    runStatus: result.runStatus,
    errorMessage: result.errorMessage ?? "",
    createdTime: formatTimestamp(result.createdTime),
    updatedTime: formatTimestamp(result.updatedTime),
  };
}


function mapOntologyAxiom(item: OntologyAxiomApiResponse): OntologyAxiomItem {
  return {
    id: item.id,
    taskId: item.taskId,
    executionMode: item.executionMode,
    sourceLayer: item.sourceLayer,
    axiomType: item.axiomType,
    subjectTerm: item.subjectTerm ?? "",
    objectTerm: item.objectTerm ?? "",
    axiomText: item.axiomText ?? "",
    payloadJson: item.payloadJson,
    createdTime: formatTimestamp(item.createdTime),
    updatedTime: formatTimestamp(item.updatedTime),
  };
}


function mapTaskStatus(status: EvaluationTaskApiResponse["status"]): "已完成" | "运行中" | "排队中" | "失败" {
  if (status === "succeeded") {
    return "已完成";
  }
  if (status === "running") {
    return "运行中";
  }
  if (status === "failed") {
    return "失败";
  }
  return "排队中";
}


function formatTimestamp(value: string): string {
  return value.replace("T", " ").slice(0, 19);
}


function formatResponseTime(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return `${(value / 1000).toFixed(2)}s`;
}


function mapDatasetStatus(status: DatasetApiResponse["status"]): "ready" | "processing" {
  if (status === "ready") {
    return "ready";
  }
  return "processing";
}


function mapDatasetLabel(label: number | null): string {
  if (label === 1) {
    return "正确";
  }
  if (label === 0) {
    return "错误";
  }
  return "未标注";
}


export async function getModels(): Promise<ModelItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/models`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch models: ${response.status}`);
    }

    const data = (await response.json()) as ModelApiResponse[];
    return data.map(mapModel);
  } catch (error) {
    console.warn("读取模型接口失败，已回退到本地演示数据。", error);
    return models;
  }
}


export type ModelConfigPayload = {
  modelName: string;
  modelCode: string;
  apiUrl: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
  status: number;
};


export async function getModelConfigs(): Promise<ModelConfigItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/model-configs`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch model configs: ${response.status}`);
    }

    const data = (await response.json()) as ModelConfigApiResponse[];
    return data.map(mapModelConfig);
  } catch (error) {
    console.warn("读取模型配置接口失败，已回退到本地演示数据。", error);
    return modelConfigs;
  }
}


export async function createModelConfig(payload: ModelConfigPayload): Promise<ModelConfigItem> {
  const response = await fetch(`${API_BASE_URL}/model-configs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`创建模型配置失败：${response.status}`);
  }

  return mapModelConfig((await response.json()) as ModelConfigApiResponse);
}


export async function updateModelConfig(
  configId: number,
  payload: ModelConfigPayload,
): Promise<ModelConfigItem> {
  const response = await fetch(`${API_BASE_URL}/model-configs/${configId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`更新模型配置失败：${response.status}`);
  }

  return mapModelConfig((await response.json()) as ModelConfigApiResponse);
}


export async function deleteModelConfig(configId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/model-configs/${configId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除模型配置失败：${response.status}`);
  }
}


export async function getEvalDatasets(datasetName = ""): Promise<EvalDatasetListItem[]> {
  try {
    const params = new URLSearchParams();
    if (datasetName.trim()) {
      params.set("datasetName", datasetName.trim());
    }
    const query = params.toString();
    const response = await fetch(`${API_BASE_URL}/eval-datasets${query ? `?${query}` : ""}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch eval datasets: ${response.status}`);
    }

    const envelope = (await response.json()) as ApiEnvelope<EvalDatasetApiResponse[]>;
    return envelope.data.map(mapEvalDataset);
  } catch (error) {
    console.warn("读取评测数据集接口失败。", error);
    return [];
  }
}


export async function uploadEvalDataset(formData: FormData): Promise<EvalDatasetUploadResult> {
  const response = await fetch(`${API_BASE_URL}/eval-datasets/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`上传评测数据集失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalDatasetUploadApiResponse>;
  return {
    dataset: mapEvalDataset(envelope.data.dataset),
    totalCount: envelope.data.totalCount,
    successCount: envelope.data.successCount,
    failedCount: envelope.data.failedCount,
    errors: envelope.data.errors,
  };
}


export async function getEvalDatasetDetail(datasetId: string): Promise<EvalDatasetListItem> {
  const response = await fetch(`${API_BASE_URL}/eval-datasets/${datasetId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评测数据集详情失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalDatasetApiResponse>;
  return mapEvalDataset(envelope.data);
}


export async function getEvalDatasetRecords(params: {
  datasetId: number;
  page?: number;
  pageSize?: number;
  axiomType?: string;
  label?: string;
  source?: string;
}): Promise<EvalDatasetRecordPage> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("pageSize", String(params.pageSize ?? 20));
  if (params.axiomType) {
    query.set("axiomType", params.axiomType);
  }
  if (params.label !== undefined && params.label !== "") {
    query.set("label", params.label);
  }
  if (params.source) {
    query.set("source", params.source);
  }

  const response = await fetch(`${API_BASE_URL}/eval-datasets/${params.datasetId}/records?${query.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评测样本失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalDatasetRecordPageApiResponse>;
  return {
    records: envelope.data.records.map(mapEvalDatasetRecord),
    total: envelope.data.total,
    page: envelope.data.page,
    pageSize: envelope.data.pageSize,
  };
}


export async function deleteEvalDataset(datasetId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/eval-datasets/${datasetId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除评测数据集失败：${response.status}`);
  }
}

export async function getEvalTasks(filters: { taskName?: string; taskStatus?: string } = {}): Promise<EvalTaskItem[]> {
  const params = new URLSearchParams();
  if (filters.taskName?.trim()) {
    params.set("taskName", filters.taskName.trim());
  }
  if (filters.taskStatus?.trim()) {
    params.set("taskStatus", filters.taskStatus.trim());
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/eval-tasks${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评估任务失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskApiResponse[]>;
  return envelope.data.map(mapEvalTask);
}


export async function createEvalTask(payload: EvalTaskPayload): Promise<EvalTaskItem> {
  const response = await fetch(`${API_BASE_URL}/eval-tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`创建评估任务失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskApiResponse>;
  return mapEvalTask(envelope.data);
}


export async function startEvalTask(taskId: number): Promise<EvalTaskItem> {
  const response = await fetch(`${API_BASE_URL}/eval-tasks/${taskId}/start`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`启动评估任务失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskApiResponse>;
  return mapEvalTask(envelope.data);
}


export async function stopEvalTask(taskId: number): Promise<EvalTaskItem> {
  const response = await fetch(`${API_BASE_URL}/eval-tasks/${taskId}/stop`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`停止评估任务失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskApiResponse>;
  return mapEvalTask(envelope.data);
}


export async function getEvalTaskDetail(taskId: string): Promise<EvalTaskDetail> {
  const response = await fetch(`${API_BASE_URL}/eval-tasks/${taskId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评估任务详情失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskDetailApiResponse>;
  return {
    task: mapEvalTask(envelope.data.task),
    dataset: envelope.data.dataset,
    model: envelope.data.model,
    prompt: envelope.data.prompt,
    metrics: envelope.data.metrics,
  };
}


export async function getEvalTaskResults(params: {
  taskId: number;
  page?: number;
  pageSize?: number;
  axiomType?: string;
  trueLabel?: string;
  predictLabel?: string;
  runStatus?: string;
}): Promise<EvalTaskResultPage> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("pageSize", String(params.pageSize ?? 20));
  if (params.axiomType) {
    query.set("axiomType", params.axiomType);
  }
  if (params.trueLabel !== undefined && params.trueLabel !== "") {
    query.set("trueLabel", params.trueLabel);
  }
  if (params.predictLabel !== undefined && params.predictLabel !== "") {
    query.set("predictLabel", params.predictLabel);
  }
  if (params.runStatus) {
    query.set("runStatus", params.runStatus);
  }

  const response = await fetch(`${API_BASE_URL}/eval-tasks/${params.taskId}/results?${query.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评估结果失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalTaskResultPageApiResponse>;
  return {
    records: envelope.data.records.map(mapEvalTaskResult),
    total: envelope.data.total,
    page: envelope.data.page,
    pageSize: envelope.data.pageSize,
  };
}


export async function deleteEvalTask(taskId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/eval-tasks/${taskId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除评估任务失败：${response.status}`);
  }
}


export async function getExplanationEvalStats(taskId: number): Promise<ExplanationEvalStats> {
  const response = await fetch(`${API_BASE_URL}/explanation-evals/tasks/${taskId}/stats`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取解释能力统计失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<ExplanationEvalStatsApiResponse>;
  return envelope.data;
}


export async function getExplanationEvalRecords(params: {
  taskId: number;
  page?: number;
  pageSize?: number;
  annotationStatus?: string;
}): Promise<ExplanationEvalPage> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("pageSize", String(params.pageSize ?? 20));
  if (params.annotationStatus) {
    query.set("annotationStatus", params.annotationStatus);
  }

  const response = await fetch(`${API_BASE_URL}/explanation-evals/tasks/${params.taskId}/records?${query.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取解释评估列表失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<ExplanationEvalPageApiResponse>;
  return {
    records: envelope.data.records.map(mapExplanationEvalItem),
    total: envelope.data.total,
    page: envelope.data.page,
    pageSize: envelope.data.pageSize,
  };
}


export async function saveExplanationEvalRecord(payload: ExplanationEvalPayload): Promise<ExplanationEvalAnnotation> {
  const response = await fetch(`${API_BASE_URL}/explanation-evals/records`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`保存解释标注失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<ExplanationEvalAnnotationApiResponse>;
  return {
    id: envelope.data.id,
    taskId: envelope.data.taskId,
    resultId: envelope.data.resultId,
    explanationCorrectLabel: envelope.data.explanationCorrectLabel,
    hallucinationLabel: envelope.data.hallucinationLabel,
    annotationStatus: envelope.data.annotationStatus,
    annotationRemark: envelope.data.annotationRemark ?? "",
    createdTime: envelope.data.createdTime ? formatTimestamp(envelope.data.createdTime) : "",
    updatedTime: envelope.data.updatedTime ? formatTimestamp(envelope.data.updatedTime) : "",
  };
}


export async function getStabilityTemplates(): Promise<StabilityTemplateMap> {
  const response = await fetch(`${API_BASE_URL}/stability-evals/templates`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取稳定性扰动模板失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<StabilityTemplateApiResponse>;
  return envelope.data;
}


export async function getStabilityEvalTasks(baseTaskId: number): Promise<StabilityEvalTaskItem[]> {
  const response = await fetch(`${API_BASE_URL}/stability-evals/base-tasks/${baseTaskId}/tasks`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取稳定性评估任务失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<StabilityEvalTaskApiResponse[]>;
  return envelope.data.map(mapStabilityEvalTask);
}


export async function createStabilityEvalTask(baseTaskId: number): Promise<StabilityEvalTaskItem> {
  const response = await fetch(`${API_BASE_URL}/stability-evals/tasks/${baseTaskId}/run`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`启动稳定性评估失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<StabilityEvalTaskApiResponse>;
  return mapStabilityEvalTask(envelope.data);
}


export async function stopStabilityEvalTask(stabilityTaskId: number): Promise<StabilityEvalTaskItem> {
  const response = await fetch(`${API_BASE_URL}/stability-evals/tasks/${stabilityTaskId}/stop`, {
    method: "POST",
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail = errorBody?.detail ? `：${errorBody.detail}` : "";
    throw new Error(`停止稳定性评估失败${detail}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<StabilityEvalTaskApiResponse>;
  return mapStabilityEvalTask(envelope.data);
}


export async function getStabilityEvalRecords(params: {
  stabilityTaskId: number;
  page?: number;
  pageSize?: number;
}): Promise<StabilityEvalRecordPage> {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("pageSize", String(params.pageSize ?? 20));

  const response = await fetch(`${API_BASE_URL}/stability-evals/tasks/${params.stabilityTaskId}/records?${query.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取稳定性评估结果失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<StabilityEvalRecordPageApiResponse>;
  return {
    records: envelope.data.records.map(mapStabilityEvalRecord),
    total: envelope.data.total,
    page: envelope.data.page,
    pageSize: envelope.data.pageSize,
  };
}


export async function getEvalReport(taskId: number): Promise<EvalReportData> {
  const response = await fetch(`${API_BASE_URL}/eval-reports/tasks/${taskId}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取评估报告失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<EvalReportApiResponse>;
  return mapEvalReport(envelope.data);
}

export type PromptTemplateConfigPayload = {
  templateName: string;
  taskType: string;
  templateType: string;
  layerName: string | null;
  templateContent: string;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntity: number;
  remark: string | null;
  status: number;
};

export type OntologyTaskItem = {
  id: number;
  taskName: string;
  taskType: string;
  executionMode: string;
  modelId: number;
  promptId: number;
  semanticPromptId: number | null;
  termPromptId: number | null;
  conceptPromptId: number | null;
  domainType: string;
  domainSwitch: number;
  chunkMetadataSwitch: number;
  inputType: string;
  fileName: string;
  filePath: string;
  totalChunkCount: number;
  successCount: number;
  failCount: number;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntityDefinition: number;
  inputText: string;
  finalPrompt: string;
  outputContent: string;
  mergedOutput: string;
  taskStatus: string;
  errorMessage: string;
  remark: string;
  createdTime: string;
  updatedTime: string;
  modelName: string;
  promptName: string;
};

export type OntologyChunkItem = {
  id: number;
  taskId: number;
  chunkId: string;
  chunkIndex: number;
  sectionTitle: string;
  pageStart: number | null;
  pageEnd: number | null;
  chunkText: string;
  createdTime: string;
  updatedTime: string;
  resultId: number | null;
  runStatus: string;
  errorMessage: string;
  classCount: number;
  propertyCount: number;
  subClassOfCount: number;
  subPropertyOfCount: number;
  domainCount: number;
  rangeCount: number;
  semanticNetworkStatus: string;
  termRefinementStatus: string;
  conceptModelingStatus: string;
};

export type OntologyChunkDetail = {
  chunk: OntologyChunkItem;
  result: OntologyChunkResultItem | null;
  layerResults: OntologyChunkResultItem[];
};

export type OntologyChunkResultItem = {
    id: number;
    taskId: number;
    chunkRecordId: number;
    executionMode: string;
    layerName: string;
    finalPrompt: string;
    outputContent: string;
    parsedOutput: unknown;
    runStatus: string;
    errorMessage: string;
    createdTime: string;
    updatedTime: string;
};

export type OntologyTaskStats = OntologyTaskStatsApiResponse;

export type OntologyAxiomItem = {
  id: number;
  taskId: number;
  executionMode: string;
  sourceLayer: string;
  axiomType: string;
  subjectTerm: string;
  objectTerm: string;
  axiomText: string;
  payloadJson: unknown;
  createdTime: string;
  updatedTime: string;
};

export type OntologyResultData = {
  task: OntologyResultApiResponse["task"];
  overview: Record<string, number | string | null>;
  axioms: OntologyAxiomItem[];
  graph: OntologyResultApiResponse["graph"];
  charts: OntologyResultApiResponse["charts"];
};

export type OntologyExportData = OntologyExportApiResponse;
export type OntologyLayerResults = OntologyLayerResultsApiResponse;

export type OntologyTaskPayload = {
  taskName: string;
  taskType: string;
  modelId: number;
  promptId: number;
  domainType: string;
  switchCount: number;
  switchDomain: number;
  switchNaming: number;
  switchEntityDefinition: number;
  inputText: string;
  remark: string | null;
};


export async function getPromptTemplateConfigs(): Promise<PromptTemplateConfigItem[]> {
  return getPromptTemplateConfigsByFilter({});
}


export async function getPromptTemplateConfigsByFilter(filters: {
  templateName?: string;
  taskType?: string;
  templateType?: string;
  layerName?: string;
}): Promise<PromptTemplateConfigItem[]> {
  try {
    const params = new URLSearchParams();
    if (filters.templateName?.trim()) {
      params.set("templateName", filters.templateName.trim());
    }
    if (filters.taskType?.trim()) {
      params.set("taskType", filters.taskType.trim());
    }
    if (filters.templateType?.trim()) {
      params.set("templateType", filters.templateType.trim());
    }
    if (filters.layerName?.trim()) {
      params.set("layerName", filters.layerName.trim());
    }
    const query = params.toString();
    const response = await fetch(`${API_BASE_URL}/prompt-templates/configs${query ? `?${query}` : ""}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch prompt template configs: ${response.status}`);
    }

    const envelope = (await response.json()) as ApiEnvelope<PromptTemplateConfigApiResponse[]>;
    return envelope.data.map(mapPromptTemplateConfig);
  } catch (error) {
    console.warn("读取提示词配置接口失败，已回退到本地演示数据。", error);
    return promptTemplateConfigs;
  }
}


export async function createPromptTemplateConfig(
  payload: PromptTemplateConfigPayload,
): Promise<PromptTemplateConfigItem> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/configs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`创建提示词配置失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<PromptTemplateConfigApiResponse>;
  return mapPromptTemplateConfig(envelope.data);
}


export async function updatePromptTemplateConfig(
  templateId: number,
  payload: PromptTemplateConfigPayload,
): Promise<PromptTemplateConfigItem> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/configs/${templateId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`更新提示词配置失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<PromptTemplateConfigApiResponse>;
  return mapPromptTemplateConfig(envelope.data);
}


export async function deletePromptTemplateConfig(templateId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/configs/${templateId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除提示词配置失败：${response.status}`);
  }
}


export async function setPromptTemplateConfigStatus(
  templateId: number,
  status: number,
): Promise<PromptTemplateConfigItem> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/configs/${templateId}/status?status=${status}`, {
    method: "PUT",
  });

  if (!response.ok) {
    throw new Error(`更新提示词状态失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<PromptTemplateConfigApiResponse>;
  return mapPromptTemplateConfig(envelope.data);
}


export async function previewPromptTemplateConfig(templateId: number): Promise<PromptTemplateConfigPreview> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/configs/${templateId}/preview`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`预览提示词失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<PromptTemplateConfigPreviewApiResponse>;
  return envelope.data;
}


export async function getOntologyTasks(filters: {
  taskName?: string;
  taskType?: string;
} = {}): Promise<OntologyTaskItem[]> {
  const params = new URLSearchParams();
  if (filters.taskName?.trim()) {
    params.set("taskName", filters.taskName.trim());
  }
  if (filters.taskType?.trim()) {
    params.set("taskType", filters.taskType.trim());
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/ontology-tasks${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`读取本体学习任务失败：${response.status}`);
  }

  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse[]>;
  return envelope.data.map(mapOntologyTask);
}


export async function createOntologyTask(payload: OntologyTaskPayload): Promise<OntologyTaskItem> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `创建本体学习任务失败：${response.status}`;
    throw new Error(message);
  }

  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse>;
  return mapOntologyTask(envelope.data);
}


export async function createOntologyBaselineTask(payload: {
  taskName: string;
  modelId: number;
  promptId: number;
  domainType: string;
  domainSwitch: number;
  chunkMetadataSwitch: number;
  remark: string;
  file: File;
}): Promise<OntologyTaskItem> {
  const formData = new FormData();
  formData.set("taskName", payload.taskName);
  formData.set("modelId", String(payload.modelId));
  formData.set("promptId", String(payload.promptId));
  formData.set("domainType", payload.domainType);
  formData.set("domainSwitch", String(payload.domainSwitch));
  formData.set("chunkMetadataSwitch", String(payload.chunkMetadataSwitch));
  formData.set("remark", payload.remark);
  formData.set("file", payload.file);

  const response = await fetch(`${API_BASE_URL}/ontology-tasks/baseline`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `创建 baseline 任务失败：${response.status}`;
    throw new Error(message);
  }

  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse>;
  return mapOntologyTask(envelope.data);
}


export async function createOntologyLayeredTask(payload: {
  taskName: string;
  modelId: number;
  semanticPromptId: number;
  termPromptId: number;
  conceptPromptId: number;
  domainType: string;
  domainSwitch: number;
  chunkMetadataSwitch: number;
  remark: string;
  file: File;
}): Promise<OntologyTaskItem> {
  const formData = new FormData();
  formData.set("taskName", payload.taskName);
  formData.set("modelId", String(payload.modelId));
  formData.set("semanticPromptId", String(payload.semanticPromptId));
  formData.set("termPromptId", String(payload.termPromptId));
  formData.set("conceptPromptId", String(payload.conceptPromptId));
  formData.set("domainType", payload.domainType);
  formData.set("domainSwitch", String(payload.domainSwitch));
  formData.set("chunkMetadataSwitch", String(payload.chunkMetadataSwitch));
  formData.set("remark", payload.remark);
  formData.set("file", payload.file);

  const response = await fetch(`${API_BASE_URL}/ontology-tasks/layered`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail ?? `创建三层学习任务失败：${response.status}`;
    throw new Error(message);
  }

  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse>;
  return mapOntologyTask(envelope.data);
}


export async function getOntologyTask(taskId: number): Promise<OntologyTaskItem> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`读取本体学习任务详情失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse>;
  return mapOntologyTask(envelope.data);
}


export async function stopOntologyTask(taskId: number): Promise<OntologyTaskItem> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}/stop`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`停止本体学习任务失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskApiResponse>;
  return mapOntologyTask(envelope.data);
}


export async function getOntologyTaskStats(taskId: number): Promise<OntologyTaskStats> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}/stats`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`读取本体学习统计失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyTaskStatsApiResponse>;
  return envelope.data;
}


export async function getOntologyTaskChunks(taskId: number): Promise<OntologyChunkItem[]> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}/chunks`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`读取 chunk 列表失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyChunkApiResponse[]>;
  return envelope.data.map(mapOntologyChunk);
}


export async function getOntologyChunkDetail(taskId: number, chunkId: number): Promise<OntologyChunkDetail> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}/chunks/${chunkId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`读取 chunk 详情失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyChunkDetailApiResponse>;
  return {
    chunk: mapOntologyChunk(envelope.data.chunk),
    result: envelope.data.result ? mapOntologyChunkResult(envelope.data.result) : null,
    layerResults: (envelope.data.layerResults ?? []).map(mapOntologyChunkResult),
  };
}


export async function getOntologyResult(taskId: number, axiomType = "all"): Promise<OntologyResultData> {
  const params = new URLSearchParams();
  if (axiomType && axiomType !== "all") {
    params.set("axiomType", axiomType);
  }
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/ontology-results/tasks/${taskId}${query ? `?${query}` : ""}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`读取本体结果失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyResultApiResponse>;
  return {
    task: {
      ...envelope.data.task,
      createdTime: formatTimestamp(envelope.data.task.createdTime),
      updatedTime: formatTimestamp(envelope.data.task.updatedTime),
    },
    overview: envelope.data.overview,
    axioms: envelope.data.axioms.map(mapOntologyAxiom),
    graph: envelope.data.graph,
    charts: envelope.data.charts,
  };
}


export async function exportOntologyResult(taskId: number, format: string): Promise<OntologyExportData> {
  const response = await fetch(`${API_BASE_URL}/ontology-results/tasks/${taskId}/export?format=${encodeURIComponent(format)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`导出本体结果失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyExportApiResponse>;
  return envelope.data;
}


export async function getOntologyLayerResults(taskId: number): Promise<OntologyLayerResults> {
  const response = await fetch(`${API_BASE_URL}/ontology-results/tasks/${taskId}/layers`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`读取分层结果失败：${response.status}`);
  }
  const envelope = (await response.json()) as ApiEnvelope<OntologyLayerResultsApiResponse>;
  return envelope.data;
}


export async function deleteOntologyTask(taskId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/ontology-tasks/${taskId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除本体学习任务失败：${response.status}`);
  }
}


export async function getDatasets(): Promise<DatasetListItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/datasets`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch datasets: ${response.status}`);
    }

    const data = (await response.json()) as DatasetApiResponse[];
    return data.map((dataset) => ({
      id: dataset.id,
      name: dataset.name,
      source: dataset.source ?? "未指定",
      samples: dataset.row_count,
      labeledSamples: dataset.has_labels ? dataset.row_count : 0,
      status: mapDatasetStatus(dataset.status),
      updatedAt: formatTimestamp(dataset.updated_at),
      fileName: dataset.file_name,
    }));
  } catch (error) {
    console.warn("读取数据集接口失败，已回退到本地演示数据。", error);
    return datasets.map((dataset) => ({
      id: dataset.id,
      name: dataset.name,
      source: dataset.source,
      samples: dataset.samples,
      labeledSamples: dataset.labeledSamples,
      status: dataset.status,
      updatedAt: dataset.updatedAt,
      fileName: null,
    }));
  }
}


export async function uploadDataset(formData: FormData): Promise<DatasetListItem> {
  const response = await fetch(`${API_BASE_URL}/datasets/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`上传数据集失败：${response.status}`);
  }

  const dataset = (await response.json()) as DatasetApiResponse;
  return {
    id: dataset.id,
    name: dataset.name,
    source: dataset.source ?? "未指定",
    samples: dataset.row_count,
    labeledSamples: dataset.has_labels ? dataset.row_count : 0,
    status: mapDatasetStatus(dataset.status),
    updatedAt: formatTimestamp(dataset.updated_at),
    fileName: dataset.file_name,
  };
}


export async function getDatasetDetail(datasetId: string): Promise<DatasetDetailData> {
  try {
    const numericId = Number(datasetId);
    const [datasetResponse, previewResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/datasets/${numericId}`, { cache: "no-store" }),
      fetch(`${API_BASE_URL}/datasets/${numericId}/preview`, { cache: "no-store" }),
    ]);

    if (!datasetResponse.ok || !previewResponse.ok) {
      throw new Error("Failed to fetch dataset detail");
    }

    const dataset = (await datasetResponse.json()) as DatasetApiResponse;
    const previewRows = (await previewResponse.json()) as DatasetPreviewApiResponse[];

    return {
      id: dataset.id,
      name: dataset.name,
      description: dataset.description ?? "暂无描述",
      source: dataset.source ?? "未指定",
      samples: dataset.row_count,
      labeledSamples: dataset.has_labels ? dataset.row_count : 0,
      status: mapDatasetStatus(dataset.status),
      fileName: dataset.file_name,
      previewRows: previewRows.map((row) => ({
        sampleId: row.sample_id,
        axiomType: row.axiom_type,
        axiomText: row.axiom_text,
        label: mapDatasetLabel(row.label),
        source: row.source ?? "未指定",
      })),
    };
  } catch (error) {
    console.warn("读取数据集详情接口失败，已回退到本地演示数据。", error);
    const fallbackDataset = datasets.find((item) => String(item.id) === datasetId) ?? datasets[0];
    return {
      id: fallbackDataset.id,
      name: fallbackDataset.name,
      description: "展示数据集元信息、公理类型覆盖情况和样本预览，适合用于论文系统界面截图。",
      source: fallbackDataset.source,
      samples: fallbackDataset.samples,
      labeledSamples: fallbackDataset.labeledSamples,
      status: fallbackDataset.status,
      fileName: null,
      previewRows: [
        { sampleId: "hard_case_0001", axiomType: "subClassOf", axiomText: "Airline ⊑ PublicTransitSystem", label: "错误", source: "hard_case" },
        { sampleId: "hard_case_0002", axiomType: "subClassOf", axiomText: "Album ⊑ MusicalWork", label: "正确", source: "hard_case" },
        { sampleId: "hard_case_0103", axiomType: "domain", axiomText: "birthPlace domain Person", label: "正确", source: "hard_case" },
        { sampleId: "hard_case_0217", axiomType: "range", axiomText: "spouse range Person", label: "正确", source: "hard_case" },
      ],
    };
  }
}


export type ModelPayload = {
  name: string;
  provider: string;
  apiKey: string;
  baseUrl: string;
  modelName: string;
  isDefault: boolean;
};


export async function createModel(payload: ModelPayload): Promise<ModelItem> {
  const response = await fetch(`${API_BASE_URL}/models`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      provider: payload.provider,
      api_key: payload.apiKey,
      base_url: payload.baseUrl,
      model_name: payload.modelName,
      is_default: payload.isDefault,
    }),
  });

  if (!response.ok) {
    throw new Error(`创建模型失败：${response.status}`);
  }

  return mapModel((await response.json()) as ModelApiResponse);
}


export async function updateModel(modelId: number, payload: ModelPayload): Promise<ModelItem> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: payload.name,
      provider: payload.provider,
      api_key: payload.apiKey,
      base_url: payload.baseUrl,
      model_name: payload.modelName,
      is_default: payload.isDefault,
    }),
  });

  if (!response.ok) {
    throw new Error(`更新模型失败：${response.status}`);
  }

  return mapModel((await response.json()) as ModelApiResponse);
}


export async function deleteModel(modelId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`删除模型失败：${response.status}`);
  }
}


async function getDatasetsForEvaluation(): Promise<DatasetApiResponse[]> {
  const response = await fetch(`${API_BASE_URL}/datasets`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.status}`);
  }
  return (await response.json()) as DatasetApiResponse[];
}


async function getPromptTemplatesForEvaluation(): Promise<PromptTemplateApiResponse[]> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch prompt templates: ${response.status}`);
  }
  return (await response.json()) as PromptTemplateApiResponse[];
}


function mapPromptTemplate(template: PromptTemplateApiResponse): PromptTemplateItem {
  return {
    id: template.id,
    name: template.name,
    templateType: template.template_type,
    content: template.content ?? "",
    description: template.description ?? "",
    isDefault: template.is_default,
  };
}


export async function getPromptTemplates(): Promise<PromptTemplateItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/prompt-templates`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch prompt templates: ${response.status}`);
    }

    const data = (await response.json()) as PromptTemplateApiResponse[];
    return data.map(mapPromptTemplate);
  } catch (error) {
    console.warn("读取提示词模板接口失败，已回退到本地演示数据。", error);
    return promptTemplates.map((item, index) => ({
      id: index + 1,
      name: item.name,
      templateType:
        index === 0 ? "basic" : index === 1 ? "instruction_enhanced" : "context_guided",
      content: `${item.name}示例内容`,
      description: item.summary,
      isDefault: index === 2,
    }));
  }
}


export async function updatePromptTemplate(
  templateId: number,
  payload: { content: string; description: string },
): Promise<PromptTemplateItem> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/${templateId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: payload.content,
      description: payload.description,
    }),
  });

  if (!response.ok) {
    throw new Error(`更新提示词模板失败：${response.status}`);
  }

  return mapPromptTemplate((await response.json()) as PromptTemplateApiResponse);
}


export async function setDefaultPromptTemplate(templateId: number): Promise<PromptTemplateItem> {
  const response = await fetch(`${API_BASE_URL}/prompt-templates/${templateId}/set-default`, {
    method: "PUT",
  });

  if (!response.ok) {
    throw new Error(`设置默认模板失败：${response.status}`);
  }

  return mapPromptTemplate((await response.json()) as PromptTemplateApiResponse);
}


export async function getEvaluationTasks(): Promise<EvaluationListItem[]> {
  try {
    const [tasksResponse, modelItems, datasetItems, templateItems] = await Promise.all([
      fetch(`${API_BASE_URL}/evaluations`, { cache: "no-store" }),
      getModels(),
      getDatasetsForEvaluation(),
      getPromptTemplatesForEvaluation(),
    ]);

    if (!tasksResponse.ok) {
      throw new Error(`Failed to fetch evaluations: ${tasksResponse.status}`);
    }

    const tasks = (await tasksResponse.json()) as EvaluationTaskApiResponse[];

    const taskItems = await Promise.all(
      tasks.map(async (task) => {
        const metricsResponse = await fetch(`${API_BASE_URL}/evaluations/${task.id}/metrics`, {
          cache: "no-store",
        });

        let overallMetrics = {
          total: 0,
          accuracy: 0,
          precision: 0,
          recall: 0,
          f1: 0,
        };

        if (metricsResponse.ok) {
          const metrics = (await metricsResponse.json()) as EvaluationMetricsApiResponse;
          overallMetrics = metrics.overall;
        }

        return {
          id: String(task.id),
          name: task.name,
          model: modelItems.find((item) => item.id === task.model_id)?.name ?? `模型 ${task.model_id}`,
          dataset: datasetItems.find((item) => item.id === task.dataset_id)?.name ?? `数据集 ${task.dataset_id}`,
          template:
            templateItems.find((item) => item.id === task.prompt_template_id)?.name ??
            promptTemplates[0]?.name ??
            `模板 ${task.prompt_template_id}`,
          status: mapTaskStatus(task.status),
          createdAt: formatTimestamp(task.created_at),
          samples: overallMetrics.total,
          accuracy: overallMetrics.accuracy,
          precision: overallMetrics.precision,
          recall: overallMetrics.recall,
          f1: overallMetrics.f1,
        };
      }),
    );

    return taskItems;
  } catch (error) {
    console.warn("读取评测任务接口失败，已回退到本地演示数据。", error);
    return evaluationJobs;
  }
}


export async function getEvaluationCreateOptions(): Promise<EvaluationCreateOptions> {
  const [modelItems, datasetItems, templateItems] = await Promise.all([
    getModels(),
    getDatasets(),
    getPromptTemplates(),
  ]);

  return {
    models: modelItems,
    datasets: datasetItems,
    templates: templateItems,
  };
}


export async function createEvaluationTask(payload: {
  datasetId: number;
  modelId: number;
  promptTemplateId: number;
}): Promise<EvaluationCreateResult> {
  const response = await fetch(`${API_BASE_URL}/evaluations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      dataset_id: payload.datasetId,
      model_id: payload.modelId,
      prompt_template_id: payload.promptTemplateId,
    }),
  });

  if (!response.ok) {
    throw new Error(`创建评测任务失败：${response.status}`);
  }

  const data = (await response.json()) as {
    task: {
      id: number;
      name: string;
      status: string;
    };
    result_count: number;
  };

  return {
    taskId: data.task.id,
    taskName: data.task.name,
    status: data.task.status,
    resultCount: data.result_count,
  };
}


export async function getEvaluationDetail(taskId: string): Promise<EvaluationDetailData> {
  try {
    const numericTaskId = Number(taskId);
    const [taskResponse, resultsResponse, metricsResponse, modelItems, datasetItems, templateItems] =
      await Promise.all([
        fetch(`${API_BASE_URL}/evaluations/${numericTaskId}`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/evaluations/${numericTaskId}/results`, { cache: "no-store" }),
        fetch(`${API_BASE_URL}/evaluations/${numericTaskId}/metrics`, { cache: "no-store" }),
        getModels(),
        getDatasetsForEvaluation(),
        getPromptTemplatesForEvaluation(),
      ]);

    if (!taskResponse.ok || !resultsResponse.ok || !metricsResponse.ok) {
      throw new Error("Failed to fetch evaluation detail");
    }

    const task = (await taskResponse.json()) as EvaluationTaskDetailApiResponse;
    const results = (await resultsResponse.json()) as EvaluationResultApiResponse[];
    const metrics = (await metricsResponse.json()) as EvaluationMetricsApiResponse;

    return {
      id: String(task.id),
      name: task.name,
      model: modelItems.find((item) => item.id === task.model_id)?.name ?? `模型 ${task.model_id}`,
      dataset: datasetItems.find((item) => item.id === task.dataset_id)?.name ?? `数据集 ${task.dataset_id}`,
      template:
        templateItems.find((item) => item.id === task.prompt_template_id)?.name ??
        promptTemplates[0]?.name ??
        `模板 ${task.prompt_template_id}`,
      status: mapTaskStatus(task.status),
      samples: metrics.overall.total,
      accuracy: metrics.overall.accuracy,
      precision: metrics.overall.precision,
      recall: metrics.overall.recall,
      f1: metrics.overall.f1,
      typeMetrics: Object.entries(metrics.by_axiom_type).map(([axiomType, value]) => ({
        axiomType,
        total: value.total,
        accuracy: value.accuracy,
        precision: value.precision,
        recall: value.recall,
        f1: value.f1,
      })),
      results: results.map((item) => ({
        sampleId: item.sample_id ?? `record_${item.dataset_record_id}`,
        axiomType: item.axiom_type ?? "--",
        axiomText: item.axiom_text ?? "--",
        judgment: item.judgment_result === "Correct" ? "正确" : "错误",
        explanation: item.explanation ?? item.raw_response ?? "未解析出解释内容",
        responseTime: formatResponseTime(item.response_time_ms),
        tokens: item.total_tokens ?? 0,
      })),
    };
  } catch (error) {
    console.warn("读取评测详情接口失败，已回退到本地演示数据。", error);
    const fallbackJob = evaluationJobs.find((item) => item.id === taskId) ?? evaluationJobs[0];
    return {
      ...fallbackJob,
      typeMetrics: evaluationTypeMetrics.map((item) => ({
        axiomType: item.axiomType,
        total: 20,
        accuracy: item.accuracy,
        precision: item.accuracy,
        recall: item.accuracy,
        f1: item.f1,
      })),
      results: evaluationResultRows,
    };
  }
}


export async function getAnnotationResults(taskId: string): Promise<AnnotationItemData[]> {
  const response = await fetch(`${API_BASE_URL}/annotations/tasks/${taskId}/results`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch annotation results: ${response.status}`);
  }

  const data = (await response.json()) as { items: AnnotationResultApiResponse[] };
  return data.items.map((item) => ({
    evaluationResultId: item.evaluation_result_id,
    sampleId: item.sample_id ?? `result_${item.evaluation_result_id}`,
    axiomType: item.axiom_type ?? "--",
    axiomText: item.axiom_text ?? "--",
    judgmentResult: item.judgment_result ?? "--",
    explanation: item.explanation ?? "未解析出解释内容",
    rawResponse: item.raw_response ?? "",
    explanationLabel: item.explanation_label,
    annotationReason: item.annotation_reason ?? "",
  }));
}


export async function submitAnnotation(payload: {
  evaluationResultId: number;
  explanationLabel: "correct" | "wrong" | "hallucination";
  annotationReason?: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/annotations/results/${payload.evaluationResultId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      explanation_label: payload.explanationLabel,
      annotation_reason: payload.annotationReason ?? "",
    }),
  });

  if (!response.ok) {
    throw new Error(`提交标注失败：${response.status}`);
  }
}


export async function getExplanationStats(): Promise<ExplanationStatsData> {
  try {
    const response = await fetch(`${API_BASE_URL}/annotations/stats`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch explanation stats: ${response.status}`);
    }

    const data = (await response.json()) as AnnotationStatsApiResponse;
    return {
      overall: {
        totalAnnotations: data.overall.total_annotations,
        correctCount: data.overall.correct_count,
        hallucinationCount: data.overall.hallucination_count,
        explanationAccuracy: data.overall.explanation_accuracy,
        hallucinationRate: data.overall.hallucination_rate,
      },
      byModel: Object.entries(data.by_model).map(([model, stats]) => ({
        model,
        totalAnnotations: stats.total_annotations,
        correctCount: stats.correct_count,
        hallucinationCount: stats.hallucination_count,
        explanationAccuracy: stats.explanation_accuracy,
        hallucinationRate: stats.hallucination_rate,
      })),
    };
  } catch (error) {
    console.warn("读取解释统计接口失败，已回退到本地演示数据。", error);
    return {
      overall: {
        totalAnnotations: 880,
        correctCount: 612,
        hallucinationCount: 96,
        explanationAccuracy: 0.695,
        hallucinationRate: 0.109,
      },
      byModel: [],
    };
  }
}


export async function getDashboardStats(): Promise<DashboardStatsData> {
  const [modelItems, datasetItems, taskItems, explanationStats] = await Promise.all([
    getModels(),
    getDatasets(),
    getEvaluationTasks(),
    getExplanationStats(),
  ]);

  return {
    modelCount: modelItems.length,
    datasetCount: datasetItems.length,
    evaluationCount: taskItems.length,
    annotationCount: explanationStats.overall.totalAnnotations,
  };
}
