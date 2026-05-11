"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";

import {
  createOntologyBaselineTask,
  createOntologyLayeredTask,
  createOntologyTask,
  deleteOntologyTask,
  getOntologyChunkDetail,
  getOntologyTask,
  getOntologyTaskChunks,
  getOntologyTaskStats,
  getOntologyTasks,
  stopOntologyTask,
  type OntologyChunkDetail,
  type OntologyChunkItem,
  type OntologyTaskStats,
  type OntologyTaskItem,
} from "@/lib/api";
import { type ModelConfigItem, type PromptTemplateConfigItem } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { OntologyResultExportPanel } from "@/components/ontology/ontology-result-export-panel";


type OntologyTaskManagerProps = {
  initialTasks: OntologyTaskItem[];
  models: ModelConfigItem[];
  prompts: PromptTemplateConfigItem[];
};

type FormState = {
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
  remark: string;
};

const DOMAIN_OPTIONS = [
  { value: "geography", label: "geography" },
  { value: "medical", label: "medical" },
  { value: "transportation", label: "transportation" },
];

const SWITCHES = [
  ["switchCount", "COUNT"] as const,
  ["switchDomain", "DOMAIN"] as const,
  ["switchNaming", "NAMING"] as const,
  ["switchEntityDefinition", "ENTITY_DEFINITION"] as const,
];


export function OntologyTaskManager({ initialTasks, models, prompts }: OntologyTaskManagerProps) {
  const resultRef = useRef<HTMLDivElement | null>(null);
  const activeModels = useMemo(() => models.filter((model) => model.status === 1), [models]);
  const configurablePrompts = useMemo(
    () =>
      prompts.filter(
        (prompt) =>
          prompt.status === 1 &&
          prompt.taskType === "configuration_optimization" &&
          prompt.templateType === "configurable",
      ),
    [prompts],
  );
  const baselinePrompts = useMemo(
    () =>
      prompts.filter(
        (prompt) =>
          prompt.status === 1 &&
          prompt.taskType === "ontology_learning" &&
          prompt.templateType === "baseline",
      ),
    [prompts],
  );
  const meaningPrompts = useMemo(() => prompts.filter((prompt) => prompt.status === 1 && prompt.taskType === "ontology_learning" && prompt.templateType === "meaning"), [prompts]);
  const termPrompts = useMemo(() => prompts.filter((prompt) => prompt.status === 1 && prompt.taskType === "ontology_learning" && prompt.templateType === "term"), [prompts]);
  const conceptPrompts = useMemo(() => prompts.filter((prompt) => prompt.status === 1 && prompt.taskType === "ontology_learning" && prompt.templateType === "concept"), [prompts]);
  const defaultPromptId = configurablePrompts[0]?.id ?? 0;
  const defaultBaselinePromptId = baselinePrompts[0]?.id ?? 0;
  const defaultMeaningPromptId = meaningPrompts[0]?.id ?? 0;
  const defaultTermPromptId = termPrompts[0]?.id ?? 0;
  const defaultConceptPromptId = conceptPrompts[0]?.id ?? 0;
  const defaultModelId = activeModels[0]?.id ?? 0;

  const [items, setItems] = useState(initialTasks);
  const [selectedTask, setSelectedTask] = useState<OntologyTaskItem | null>(initialTasks[0] ?? null);
  const [baselineTask, setBaselineTask] = useState<OntologyTaskItem | null>(
    initialTasks.find((task) => task.taskType === "ontology_learning" && task.executionMode === "baseline") ?? null,
  );
  const [baselineChunks, setBaselineChunks] = useState<OntologyChunkItem[]>([]);
  const [baselineStats, setBaselineStats] = useState<OntologyTaskStats | null>(null);
  const [chunkDetail, setChunkDetail] = useState<OntologyChunkDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"configuration_optimization" | "ontology_learning">("configuration_optimization");
  const [progress, setProgress] = useState(0);
  const [isPending, startTransition] = useTransition();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [filterName, setFilterName] = useState("");
  const [formState, setFormState] = useState<FormState>({
    taskName: "配置优化实验",
    taskType: "configuration_optimization",
    modelId: defaultModelId,
    promptId: defaultPromptId,
    domainType: "geography",
    switchCount: 0,
    switchDomain: 0,
    switchNaming: 0,
    switchEntityDefinition: 0,
    inputText: "",
    remark: "",
  });
  const [baselineForm, setBaselineForm] = useState({
    taskName: "baseline 本体学习实验",
    modelId: defaultModelId,
    promptId: defaultBaselinePromptId,
    domainType: "geography",
    domainSwitch: 1,
    chunkMetadataSwitch: 1,
    remark: "",
  });
  const [baselineFile, setBaselineFile] = useState<File | null>(null);
  const [learningMode, setLearningMode] = useState<"baseline" | "layered">("baseline");
  const [layeredForm, setLayeredForm] = useState({
    taskName: "三层本体学习实验",
    modelId: defaultModelId,
    semanticPromptId: defaultMeaningPromptId,
    termPromptId: defaultTermPromptId,
    conceptPromptId: defaultConceptPromptId,
    domainType: "geography",
    domainSwitch: 1,
    chunkMetadataSwitch: 1,
    remark: "",
  });
  const [layeredFile, setLayeredFile] = useState<File | null>(null);

  useEffect(() => {
    if (formState.modelId === 0 && defaultModelId > 0) {
      setFormState((current) => ({ ...current, modelId: defaultModelId }));
    }
    if (formState.promptId === 0 && defaultPromptId > 0) {
      setFormState((current) => ({ ...current, promptId: defaultPromptId }));
    }
    if (baselineForm.modelId === 0 && defaultModelId > 0) {
      setBaselineForm((current) => ({ ...current, modelId: defaultModelId }));
    }
    if (baselineForm.promptId === 0 && defaultBaselinePromptId > 0) {
      setBaselineForm((current) => ({ ...current, promptId: defaultBaselinePromptId }));
    }
    if (layeredForm.modelId === 0 && defaultModelId > 0) {
      setLayeredForm((current) => ({ ...current, modelId: defaultModelId }));
    }
    if (layeredForm.semanticPromptId === 0 && defaultMeaningPromptId > 0) {
      setLayeredForm((current) => ({ ...current, semanticPromptId: defaultMeaningPromptId }));
    }
    if (layeredForm.termPromptId === 0 && defaultTermPromptId > 0) {
      setLayeredForm((current) => ({ ...current, termPromptId: defaultTermPromptId }));
    }
    if (layeredForm.conceptPromptId === 0 && defaultConceptPromptId > 0) {
      setLayeredForm((current) => ({ ...current, conceptPromptId: defaultConceptPromptId }));
    }
  }, [defaultModelId, defaultPromptId, defaultBaselinePromptId, defaultMeaningPromptId, defaultTermPromptId, defaultConceptPromptId, formState.modelId, formState.promptId, baselineForm.modelId, baselineForm.promptId, layeredForm.modelId, layeredForm.semanticPromptId, layeredForm.termPromptId, layeredForm.conceptPromptId]);

  useEffect(() => {
    if (!baselineTask?.id) {
      return;
    }
    void refreshBaselineDetail(baselineTask.id);
    if (!["pending", "running", "stopping"].includes(baselineTask.taskStatus)) {
      return;
    }
    const timer = window.setInterval(async () => {
      const latest = await getOntologyTask(baselineTask.id);
      setBaselineTask(latest);
      setItems((current) => [latest, ...current.filter((item) => item.id !== latest.id)]);
      await refreshBaselineDetail(latest.id);
      if (!["pending", "running", "stopping"].includes(latest.taskStatus)) {
        window.clearInterval(timer);
      }
    }, 1800);
    return () => window.clearInterval(timer);
  }, [baselineTask?.id, baselineTask?.taskStatus]);

  useEffect(() => {
    if (!isPending) {
      return;
    }
    setProgress(12);
    const timer = window.setInterval(() => {
      setProgress((current) => Math.min(current + 8, 88));
    }, 600);
    return () => window.clearInterval(timer);
  }, [isPending]);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setFormState((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function updateBaselineField<K extends keyof typeof baselineForm>(key: K, value: (typeof baselineForm)[K]) {
    setBaselineForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function updateLayeredField<K extends keyof typeof layeredForm>(key: K, value: (typeof layeredForm)[K]) {
    setLayeredForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function toggleSwitch(key: (typeof SWITCHES)[number][0]) {
    updateField(key, formState[key] === 1 ? 0 : 1);
  }

  function handleRun(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (formState.taskType !== "configuration_optimization") {
      setErrorMessage("当前版本先支持配置优化实验。");
      return;
    }
    if (!formState.modelId) {
      setErrorMessage("请先配置并选择一个已启用模型。");
      return;
    }
    if (!formState.promptId) {
      setErrorMessage("请先在提示词配置中新增并启用“配置优化统一模板”。");
      return;
    }
    if (!formState.inputText.trim()) {
      setErrorMessage("请粘贴摘要文本。");
      return;
    }

    startTransition(async () => {
      try {
        const task = await createOntologyTask({
          taskName: formState.taskName.trim(),
          taskType: "configuration_optimization",
          modelId: formState.modelId,
          promptId: formState.promptId,
          domainType: formState.domainType,
          switchCount: formState.switchCount,
          switchDomain: formState.switchDomain,
          switchNaming: formState.switchNaming,
          switchEntityDefinition: formState.switchEntityDefinition,
          inputText: formState.inputText.trim(),
          remark: formState.remark.trim() || null,
        });
        setProgress(100);
        setItems((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        setSelectedTask(task);
      } catch (error) {
        setProgress(0);
        setErrorMessage(error instanceof Error ? error.message : "任务执行失败。");
      }
    });
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getOntologyTasks({
          taskName: filterName,
          taskType: "configuration_optimization",
        });
        setItems(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "查询失败。");
      }
    });
  }

  function handleSelectTask(task: OntologyTaskItem) {
    setSelectedTask(task);
    window.setTimeout(() => {
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
  }

  async function refreshBaselineDetail(taskId: number) {
    const [stats, chunks] = await Promise.all([
      getOntologyTaskStats(taskId),
      getOntologyTaskChunks(taskId),
    ]);
    setBaselineStats(stats);
    setBaselineChunks(chunks);
  }

  function handleRunBaseline(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    if (!baselineForm.modelId) {
      setErrorMessage("请先选择已启用模型。");
      return;
    }
    if (!baselineForm.promptId) {
      setErrorMessage("请先在提示词配置中新增并启用 baseline 提示词。");
      return;
    }
    if (!baselineFile) {
      setErrorMessage("请上传 PDF 文件。");
      return;
    }
    startTransition(async () => {
      try {
        const task = await createOntologyBaselineTask({ ...baselineForm, file: baselineFile });
        setItems((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        setBaselineTask(task);
        setActiveTab("ontology_learning");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "baseline 任务创建失败。");
      }
    });
  }

  function handleRunLayered(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    if (!layeredForm.modelId) {
      setErrorMessage("请先选择已启用模型。");
      return;
    }
    if (!layeredForm.semanticPromptId || !layeredForm.termPromptId || !layeredForm.conceptPromptId) {
      setErrorMessage("请先选择语义网络层、术语精化层和概念建模层提示词。");
      return;
    }
    if (!layeredFile) {
      setErrorMessage("请上传 PDF 文件。");
      return;
    }
    startTransition(async () => {
      try {
        const task = await createOntologyLayeredTask({ ...layeredForm, file: layeredFile });
        setItems((current) => [task, ...current.filter((item) => item.id !== task.id)]);
        setBaselineTask(task);
        setActiveTab("ontology_learning");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "三层学习任务创建失败。");
      }
    });
  }

  function handleStopBaseline() {
    if (!baselineTask) {
      return;
    }
    startTransition(async () => {
      try {
        const task = await stopOntologyTask(baselineTask.id);
        setBaselineTask(task);
        setItems((current) => [task, ...current.filter((item) => item.id !== task.id)]);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "停止任务失败。");
      }
    });
  }

  async function handleSelectBaselineTask(task: OntologyTaskItem) {
    setBaselineTask(task);
    await refreshBaselineDetail(task.id);
  }

  async function handleChunkDetail(chunk: OntologyChunkItem) {
    if (!baselineTask) {
      return;
    }
    const detail = await getOntologyChunkDetail(baselineTask.id, chunk.id);
    setChunkDetail(detail);
  }

  function handleDelete(task: OntologyTaskItem) {
    const confirmed = window.confirm(`确认删除任务“${task.taskName}”吗？`);
    if (!confirmed) {
      return;
    }
    startTransition(async () => {
      try {
        await deleteOntologyTask(task.id);
        setItems((current) => current.filter((item) => item.id !== task.id));
        if (selectedTask?.id === task.id) {
          setSelectedTask(null);
        }
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "删除失败。");
      }
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex rounded-2xl border border-line bg-white/70 p-1 shadow-sm">
        <button
          type="button"
          onClick={() => setActiveTab("configuration_optimization")}
          className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
            activeTab === "configuration_optimization"
              ? "bg-sage text-white shadow-sm"
              : "text-slate-600 hover:bg-white"
          }`}
        >
          配置优化
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("ontology_learning")}
          className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
            activeTab === "ontology_learning"
              ? "bg-sage text-white shadow-sm"
              : "text-slate-600 hover:bg-white"
          }`}
        >
          本体学习
        </button>
      </div>

      {activeTab === "ontology_learning" ? (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-ink">本体学习实验</h3>
                <p className="mt-1 text-sm text-slate-600">
                  支持 baseline 与三层学习两种执行模式。三层学习按语义网络层、术语精化层、概念建模层严格串行执行。
                </p>
              </div>
              <Badge variant="success">{learningMode === "baseline" ? "PDF 分块 baseline" : "三层学习"}</Badge>
            </div>

            <div className="mt-5 flex rounded-2xl border border-line bg-white/70 p-1">
              <button type="button" onClick={() => setLearningMode("baseline")} className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${learningMode === "baseline" ? "bg-sage text-white shadow-sm" : "text-slate-600 hover:bg-white"}`}>
                baseline
              </button>
              <button type="button" onClick={() => setLearningMode("layered")} className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${learningMode === "layered" ? "bg-sage text-white shadow-sm" : "text-slate-600 hover:bg-white"}`}>
                三层学习
              </button>
            </div>

            {learningMode === "baseline" ? (
            <form className="mt-6 space-y-5" onSubmit={handleRunBaseline}>
              <div className="grid gap-4 lg:grid-cols-3">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">任务名称</span>
                  <input className="paper-input" value={baselineForm.taskName} onChange={(event) => updateBaselineField("taskName", event.target.value)} required />
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">执行模式</span>
                  <select className="paper-input" value="baseline" disabled>
                    <option value="baseline">baseline</option>
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">领域选择</span>
                  <select className="paper-input" value={baselineForm.domainType} onChange={(event) => updateBaselineField("domainType", event.target.value)}>
                    {DOMAIN_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模型选择</span>
                  <select className="paper-input" value={baselineForm.modelId} onChange={(event) => updateBaselineField("modelId", Number(event.target.value))} required>
                    {activeModels.length === 0 ? <option value={0}>暂无启用模型</option> : null}
                    {activeModels.map((model) => <option key={model.id} value={model.id}>{model.modelName}</option>)}
                  </select>
                </label>
                <label className="space-y-2 lg:col-span-2">
                  <span className="text-sm font-medium text-ink">baseline 提示词模板</span>
                  <select className="paper-input" value={baselineForm.promptId} onChange={(event) => updateBaselineField("promptId", Number(event.target.value))} required>
                    {baselinePrompts.length === 0 ? <option value={0}>暂无 baseline 提示词</option> : null}
                    {baselinePrompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.templateName}</option>)}
                  </select>
                </label>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <SwitchBox label="启用领域上下文" value={baselineForm.domainSwitch} onClick={() => updateBaselineField("domainSwitch", baselineForm.domainSwitch === 1 ? 0 : 1)} />
                <SwitchBox label="启用分块元信息" value={baselineForm.chunkMetadataSwitch} onClick={() => updateBaselineField("chunkMetadataSwitch", baselineForm.chunkMetadataSwitch === 1 ? 0 : 1)} />
              </div>

              <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">上传 PDF</span>
                  <input className="paper-input" type="file" accept="application/pdf,.pdf" onChange={(event) => setBaselineFile(event.target.files?.[0] ?? null)} required />
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">备注</span>
                  <input className="paper-input" value={baselineForm.remark} onChange={(event) => updateBaselineField("remark", event.target.value)} placeholder="例如：baseline geography 论文测试" />
                </label>
              </div>

              {errorMessage ? <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

              <div className="space-y-3">
                {baselineTask && ["pending", "running", "stopping"].includes(baselineTask.taskStatus) ? (
                  <ProgressBlock task={baselineTask} />
                ) : null}
                <div className="flex gap-3">
                  <Button type="submit" variant="secondary" disabled={isPending || baselineForm.promptId === 0}>
                    {isPending ? "提交中..." : "开始运行 baseline"}
                  </Button>
                  <Button type="button" variant="outline" disabled={!baselineTask || !["pending", "running"].includes(baselineTask.taskStatus)} onClick={handleStopBaseline}>
                    终止运行
                  </Button>
                </div>
              </div>
            </form>
            ) : (
            <form className="mt-6 space-y-5" onSubmit={handleRunLayered}>
              <div className="grid gap-4 lg:grid-cols-3">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">任务名称</span>
                  <input className="paper-input" value={layeredForm.taskName} onChange={(event) => updateLayeredField("taskName", event.target.value)} required />
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">执行模式</span>
                  <select className="paper-input" value="layered" disabled>
                    <option value="layered">三层学习</option>
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">领域选择</span>
                  <select className="paper-input" value={layeredForm.domainType} onChange={(event) => updateLayeredField("domainType", event.target.value)}>
                    {DOMAIN_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模型选择</span>
                  <select className="paper-input" value={layeredForm.modelId} onChange={(event) => updateLayeredField("modelId", Number(event.target.value))} required>
                    {activeModels.length === 0 ? <option value={0}>暂无启用模型</option> : null}
                    {activeModels.map((model) => <option key={model.id} value={model.id}>{model.modelName}</option>)}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">语义网络层提示词</span>
                  <select className="paper-input" value={layeredForm.semanticPromptId} onChange={(event) => updateLayeredField("semanticPromptId", Number(event.target.value))} required>
                    {meaningPrompts.length === 0 ? <option value={0}>暂无语义网络层提示词</option> : null}
                    {meaningPrompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.templateName}</option>)}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">术语精化层提示词</span>
                  <select className="paper-input" value={layeredForm.termPromptId} onChange={(event) => updateLayeredField("termPromptId", Number(event.target.value))} required>
                    {termPrompts.length === 0 ? <option value={0}>暂无术语精化层提示词</option> : null}
                    {termPrompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.templateName}</option>)}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">概念建模层提示词</span>
                  <select className="paper-input" value={layeredForm.conceptPromptId} onChange={(event) => updateLayeredField("conceptPromptId", Number(event.target.value))} required>
                    {conceptPrompts.length === 0 ? <option value={0}>暂无概念建模层提示词</option> : null}
                    {conceptPrompts.map((prompt) => <option key={prompt.id} value={prompt.id}>{prompt.templateName}</option>)}
                  </select>
                </label>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <SwitchBox label="启用领域上下文" value={layeredForm.domainSwitch} onClick={() => updateLayeredField("domainSwitch", layeredForm.domainSwitch === 1 ? 0 : 1)} />
                <SwitchBox label="启用分块元信息" value={layeredForm.chunkMetadataSwitch} onClick={() => updateLayeredField("chunkMetadataSwitch", layeredForm.chunkMetadataSwitch === 1 ? 0 : 1)} />
              </div>

              <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">上传 PDF</span>
                  <input className="paper-input" type="file" accept="application/pdf,.pdf" onChange={(event) => setLayeredFile(event.target.files?.[0] ?? null)} required />
                </label>
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">备注</span>
                  <input className="paper-input" value={layeredForm.remark} onChange={(event) => updateLayeredField("remark", event.target.value)} placeholder="例如：三层学习 geography 论文测试" />
                </label>
              </div>

              {errorMessage ? <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

              <div className="space-y-3">
                {baselineTask && ["pending", "running", "stopping"].includes(baselineTask.taskStatus) ? <ProgressBlock task={baselineTask} /> : null}
                <div className="flex gap-3">
                  <Button type="submit" variant="secondary" disabled={isPending || layeredForm.semanticPromptId === 0 || layeredForm.termPromptId === 0 || layeredForm.conceptPromptId === 0}>
                    {isPending ? "提交中..." : "开始运行三层学习"}
                  </Button>
                  <Button type="button" variant="outline" disabled={!baselineTask || !["pending", "running"].includes(baselineTask.taskStatus)} onClick={handleStopBaseline}>
                    终止运行
                  </Button>
                </div>
              </div>
            </form>
            )}
          </Card>

          {baselineTask ? (
            <BaselineResultPanel
              task={baselineTask}
              stats={baselineStats}
              chunks={baselineChunks}
              onChunkDetail={handleChunkDetail}
            />
          ) : null}

          <BaselineTaskTable
            tasks={items.filter((task) => task.taskType === "ontology_learning" && ["baseline", "layered"].includes(task.executionMode))}
            onView={handleSelectBaselineTask}
            onDelete={handleDelete}
          />

          {chunkDetail ? <ChunkDetailDialog detail={chunkDetail} onClose={() => setChunkDetail(null)} /> : null}
        </div>
      ) : null}

      {activeTab === "configuration_optimization" ? (
      <>
      <Card className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-ink">新建本体学习任务</h3>
            <p className="mt-1 text-sm text-slate-600">
              当前实现配置优化实验：手动输入摘要文本，按四个开关动态组装最终提示词并调用模型。
            </p>
          </div>
          <Badge variant="success">配置优化实验</Badge>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleRun}>
          <div className="grid gap-4 lg:grid-cols-3">
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">任务名称</span>
              <input
                className="paper-input"
                value={formState.taskName}
                onChange={(event) => updateField("taskName", event.target.value)}
                required
              />
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">任务类型</span>
              <select
                className="paper-input"
                value={formState.taskType}
                onChange={(event) => updateField("taskType", event.target.value)}
              >
                <option value="configuration_optimization">配置优化实验</option>
                <option value="ontology_learning">本体学习实验</option>
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">模型选择</span>
              <select
                className="paper-input"
                value={formState.modelId}
                onChange={(event) => updateField("modelId", Number(event.target.value))}
                required
              >
                {activeModels.length === 0 ? <option value={0}>暂无启用模型</option> : null}
                {activeModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.modelName}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2 lg:col-span-2">
              <span className="text-sm font-medium text-ink">提示词模板</span>
              <select
                className="paper-input"
                value={formState.promptId}
                onChange={(event) => updateField("promptId", Number(event.target.value))}
                required
              >
                {configurablePrompts.length === 0 ? <option value={0}>暂无配置优化统一模板</option> : null}
                {configurablePrompts.map((prompt) => (
                  <option key={prompt.id} value={prompt.id}>
                    {prompt.templateName}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2">
              <span className="text-sm font-medium text-ink">领域选择</span>
              <select
                className="paper-input"
                value={formState.domainType}
                onChange={(event) => updateField("domainType", event.target.value)}
              >
                {DOMAIN_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {formState.taskType === "ontology_learning" ? (
            <div className="rounded-2xl border border-line bg-white/70 px-4 py-3 text-sm text-slate-600">
              本体学习实验入口已预留。当前版本先实现“配置优化实验”，请选择配置优化实验后运行。
            </div>
          ) : null}

          <div className="grid gap-3 md:grid-cols-4">
            {SWITCHES.map(([key, label]) => (
              <div key={key} className="flex items-center justify-between rounded-2xl border border-line bg-white/80 px-4 py-3">
                <span className="text-sm font-medium text-ink">{label}</span>
                <button
                  type="button"
                  onClick={() => toggleSwitch(key)}
                  className={`relative h-7 w-14 rounded-full transition ${
                    formState[key] === 1 ? "bg-sage" : "bg-slate-300"
                  }`}
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

          <label className="space-y-2 block">
            <span className="text-sm font-medium text-ink">摘要文本</span>
            <textarea
              className="w-full rounded-2xl border border-line bg-white/90 px-4 py-4 text-sm leading-7 text-ink shadow-sm outline-none transition focus:border-sage focus:ring-4 focus:ring-sage/10 min-h-[220px]"
              value={formState.inputText}
              onChange={(event) => updateField("inputText", event.target.value)}
              placeholder="在这里粘贴论文摘要文本"
              required
            />
          </label>

          <label className="space-y-2 block">
            <span className="text-sm font-medium text-ink">备注</span>
            <input
              className="paper-input"
              value={formState.remark}
              onChange={(event) => updateField("remark", event.target.value)}
              placeholder="例如：baseline / round1 / count+domain"
            />
          </label>

          {errorMessage ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="space-y-3">
            {isPending ? (
              <div className="rounded-2xl border border-line bg-white/70 p-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-ink">运行中，正在调用模型并保存最终提示词</span>
                  <span className="text-slate-500">{progress}%</span>
                </div>
                <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-sage transition-all" style={{ width: `${progress}%` }} />
                </div>
              </div>
            ) : null}
            <Button type="submit" variant="secondary" disabled={isPending || formState.taskType !== "configuration_optimization"}>
              {isPending ? "运行中..." : "开始运行"}
            </Button>
          </div>
        </form>
      </Card>

      {selectedTask ? (
        <div ref={resultRef}>
        <Card className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-ink">任务结果</h3>
              <p className="mt-1 text-sm text-slate-600">
                {selectedTask.taskName} · {selectedTask.modelName} · {selectedTask.domainType}
              </p>
            </div>
            <Badge variant={selectedTask.taskStatus === "completed" ? "success" : selectedTask.taskStatus === "failed" ? "warning" : "muted"}>
              {formatStatus(selectedTask.taskStatus)}
            </Badge>
          </div>

          <ResultSummary task={selectedTask} />

          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <TextBlock title="最终组装提示词" value={selectedTask.finalPrompt || "暂无最终提示词"} />
            <TextBlock title="格式化模型输出" value={formatModelOutput(selectedTask.outputContent || selectedTask.errorMessage || "暂无输出")} />
          </div>
          <AxiomTable task={selectedTask} />
        </Card>
        </div>
      ) : null}

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-6 py-5">
          <div>
            <h3 className="text-lg font-semibold text-ink">配置优化实验任务记录</h3>
            <p className="text-sm text-slate-600">查看历史任务的开关组合、运行状态、最终提示词和输出结果。</p>
          </div>
        </div>
        <form className="flex gap-3 border-b border-line bg-white/40 px-6 py-4" onSubmit={handleSearch}>
          <input
            className="paper-input max-w-md"
            value={filterName}
            onChange={(event) => setFilterName(event.target.value)}
            placeholder="按任务名称搜索"
          />
          <Button type="submit" variant="secondary" disabled={isPending}>
            查询
          </Button>
        </form>
        <div className="overflow-x-auto">
          <table className="paper-table min-w-[980px]">
            <thead>
              <tr>
                <th>ID</th>
                <th>任务名称</th>
                <th>模型</th>
                <th>领域</th>
                <th>开关</th>
                <th>状态</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-slate-500">
                    暂无配置优化实验任务。
                  </td>
                </tr>
              ) : (
                items.map((task) => (
                  <tr key={task.id}>
                    <td>{task.id}</td>
                    <td>
                      <p className="font-medium text-ink">{task.taskName}</p>
                      <p className="mt-1 max-w-[260px] truncate text-xs text-slate-500">{task.promptName}</p>
                    </td>
                    <td>{task.modelName}</td>
                    <td>{task.domainType}</td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        <SmallSwitch label="C" value={task.switchCount} />
                        <SmallSwitch label="D" value={task.switchDomain} />
                        <SmallSwitch label="N" value={task.switchNaming} />
                        <SmallSwitch label="E" value={task.switchEntityDefinition} />
                      </div>
                    </td>
                    <td>
                      <Badge variant={task.taskStatus === "completed" ? "success" : task.taskStatus === "failed" ? "warning" : "muted"}>
                        {formatStatus(task.taskStatus)}
                      </Badge>
                    </td>
                    <td>{task.updatedTime}</td>
                    <td>
                      <div className="flex gap-2">
                        <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => handleSelectTask(task)}>
                          查看
                        </Button>
                        <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => handleDelete(task)}>
                          删除
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
      </>
      ) : null}
    </div>
  );
}


function SmallSwitch({ label, value }: { label: string; value: number }) {
  return (
    <span className={`rounded-full px-2 py-1 text-xs ${value === 1 ? "bg-sage/15 text-sageDark" : "bg-slate-100 text-slate-500"}`}>
      {label}:{value === 1 ? "ON" : "OFF"}
    </span>
  );
}


function SwitchBox({ label, value, onClick }: { label: string; value: number; onClick: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-line bg-white/80 px-4 py-3">
      <span className="text-sm font-medium text-ink">{label}</span>
      <button type="button" onClick={onClick} className={`relative h-7 w-14 rounded-full transition ${value === 1 ? "bg-sage" : "bg-slate-300"}`}>
        <span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition ${value === 1 ? "left-8" : "left-1"}`} />
      </button>
    </div>
  );
}


function ProgressBlock({ task }: { task: OntologyTaskItem }) {
  const total = Math.max(1, task.totalChunkCount);
  const finished = task.successCount + task.failCount;
  const percent = task.totalChunkCount > 0 ? Math.round((finished / total) * 100) : 8;
  return (
    <div className="rounded-2xl border border-line bg-white/70 p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-ink">运行中：已完成 {finished} / {task.totalChunkCount || "解析中"} 个 chunk</span>
        <span className="text-slate-500">{percent}%</span>
      </div>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-sage transition-all" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}


function BaselineResultPanel({
  task,
  stats,
  chunks,
  onChunkDetail,
}: {
  task: OntologyTaskItem;
  stats: OntologyTaskStats | null;
  chunks: OntologyChunkItem[];
  onChunkDetail: (chunk: OntologyChunkItem) => void;
}) {
  const mergedText = formatModelOutput(task.mergedOutput || task.outputContent || "");
  const elementStats = stats
    ? [
        ["classes", stats.classCount],
        ["properties", stats.propertyCount],
        ["subClassOf", stats.subClassOfCount],
        ["subPropertyOf", stats.subPropertyOfCount],
        ["domain", stats.domainCount],
        ["range", stats.rangeCount],
      ]
    : [];
  const maxValue = Math.max(1, ...elementStats.map(([, value]) => Number(value)));

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">{task.executionMode === "layered" ? "三层学习任务详情" : "baseline 任务详情"}</h3>
          <p className="mt-1 text-sm text-slate-600">{task.taskName} · {task.modelName} · {task.fileName || "未记录文件名"}</p>
        </div>
        <Badge variant={task.taskStatus === "completed" || task.taskStatus === "partial_success" ? "success" : task.taskStatus === "failed" ? "warning" : "muted"}>
          {formatStatus(task.taskStatus)}
        </Badge>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="分块总数" value={String(task.totalChunkCount)} />
        <StatCard label="成功块数" value={String(task.successCount)} />
        <StatCard label="失败块数" value={String(task.failCount)} />
        <StatCard label="领域上下文" value={task.domainSwitch === 1 ? "ON" : "OFF"} />
        <StatCard label="分块元信息" value={task.chunkMetadataSwitch === 1 ? "ON" : "OFF"} />
        <StatCard label="领域" value={task.domainType} />
      </div>
      {task.executionMode === "layered" && stats ? (
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <StatCard label="第一层成功块数" value={String(stats.semanticNetworkSuccessCount)} />
          <StatCard label="第二层成功块数" value={String(stats.termRefinementSuccessCount)} />
          <StatCard label="第三层成功块数" value={String(stats.conceptModelingSuccessCount)} />
        </div>
      ) : null}

      {stats ? (
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div className="rounded-2xl border border-line bg-white/75 p-4">
            <p className="text-sm font-medium text-slate-500">任务级本体元素统计图</p>
            <div className="mt-4 space-y-3">
              {elementStats.map(([label, value]) => (
                <div key={label} className="grid grid-cols-[120px_1fr_48px] items-center gap-3 text-sm">
                  <span className="text-slate-600">{label}</span>
                  <div className="h-3 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-sage" style={{ width: `${(Number(value) / maxValue) * 100}%` }} />
                  </div>
                  <span className="text-right font-medium text-ink">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-line bg-white/75 p-4">
            <p className="text-sm font-medium text-slate-500">{task.executionMode === "layered" ? "三层执行状态图" : "chunk 级执行统计图"}</p>
            <div className="mt-6 flex h-48 items-end gap-1 overflow-x-auto">
              {chunks.map((chunk) => {
                const total = chunk.classCount + chunk.propertyCount + chunk.subClassOfCount + chunk.subPropertyOfCount + chunk.domainCount + chunk.rangeCount;
                const height = Math.max(8, Math.min(180, total * 6));
                return (
                  <div key={chunk.id} title={`${chunk.chunkId}: ${total}`} className="flex min-w-4 flex-col items-center justify-end">
                    <div className={chunk.runStatus === "success" ? "w-3 rounded-t bg-sage" : "w-3 rounded-t bg-amber-400"} style={{ height }} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}

      <ChunkTable chunks={chunks} onDetail={onChunkDetail} />

      <div className="mt-5">
        <TextBlock title="任务级聚合结果 mergedOutput" value={mergedText || "暂无聚合结果"} />
      </div>

      {["completed", "partial_success", "stopped"].includes(task.taskStatus) && task.mergedOutput ? (
        <div className="mt-5">
          <OntologyResultExportPanel task={task} />
        </div>
      ) : null}
    </Card>
  );
}


function ChunkTable({ chunks, onDetail }: { chunks: OntologyChunkItem[]; onDetail: (chunk: OntologyChunkItem) => void }) {
  const isLayered = chunks.some((chunk) => chunk.semanticNetworkStatus || chunk.termRefinementStatus || chunk.conceptModelingStatus);
  if (chunks.length === 0) {
    return <p className="mt-5 rounded-2xl border border-line bg-white/70 p-4 text-sm text-slate-500">暂无 chunk 结果。</p>;
  }
  return (
    <div className="mt-5 overflow-hidden rounded-2xl border border-line bg-white/75">
      <div className="border-b border-line px-4 py-3">
        <p className="text-sm font-medium text-slate-500">chunk 结果表</p>
      </div>
      <div className="overflow-x-auto">
        <table className="paper-table min-w-[1180px]">
          <thead>
            <tr>
              <th>chunk</th>
              <th>页码</th>
              <th>文本摘要</th>
              <th>类</th>
              <th>属性</th>
              <th>subClassOf</th>
              <th>subPropertyOf</th>
              <th>domain</th>
              <th>range</th>
              {isLayered ? <th>第一层</th> : null}
              {isLayered ? <th>第二层</th> : null}
              {isLayered ? <th>第三层</th> : null}
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {chunks.map((chunk) => (
              <tr key={chunk.id}>
                <td>{chunk.chunkId}</td>
                <td>{chunk.pageStart || "--"}-{chunk.pageEnd || "--"}</td>
                <td><p className="max-w-[260px] truncate">{chunk.chunkText}</p></td>
                <td>{chunk.classCount}</td>
                <td>{chunk.propertyCount}</td>
                <td>{chunk.subClassOfCount}</td>
                <td>{chunk.subPropertyOfCount}</td>
                <td>{chunk.domainCount}</td>
                <td>{chunk.rangeCount}</td>
                {isLayered ? <td><Badge variant={chunk.semanticNetworkStatus === "success" ? "success" : chunk.semanticNetworkStatus === "failed" ? "warning" : "muted"}>{formatStatus(chunk.semanticNetworkStatus || "pending")}</Badge></td> : null}
                {isLayered ? <td><Badge variant={chunk.termRefinementStatus === "success" ? "success" : chunk.termRefinementStatus === "failed" ? "warning" : "muted"}>{formatStatus(chunk.termRefinementStatus || "pending")}</Badge></td> : null}
                {isLayered ? <td><Badge variant={chunk.conceptModelingStatus === "success" ? "success" : chunk.conceptModelingStatus === "failed" ? "warning" : "muted"}>{formatStatus(chunk.conceptModelingStatus || "pending")}</Badge></td> : null}
                <td><Badge variant={chunk.runStatus === "success" ? "success" : chunk.runStatus === "failed" ? "warning" : "muted"}>{formatStatus(chunk.runStatus)}</Badge></td>
                <td><Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => onDetail(chunk)}>详情</Button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


function BaselineTaskTable({ tasks, onView, onDelete }: { tasks: OntologyTaskItem[]; onView: (task: OntologyTaskItem) => void; onDelete: (task: OntologyTaskItem) => void }) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-line px-6 py-5">
        <h3 className="text-lg font-semibold text-ink">本体学习任务记录</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="paper-table min-w-[960px]">
          <thead>
            <tr>
              <th>ID</th>
              <th>任务名称</th>
              <th>模型</th>
              <th>模式</th>
              <th>领域</th>
              <th>PDF</th>
              <th>进度</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr><td colSpan={9} className="py-10 text-center text-slate-500">暂无本体学习任务。</td></tr>
            ) : tasks.map((task) => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>{task.taskName}</td>
                <td>{task.modelName}</td>
                <td>{task.executionMode === "layered" ? "三层学习" : "baseline"}</td>
                <td>{task.domainType}</td>
                <td>{task.fileName || "--"}</td>
                <td>{task.successCount + task.failCount}/{task.totalChunkCount}</td>
                <td><Badge variant={task.taskStatus === "completed" || task.taskStatus === "partial_success" ? "success" : task.taskStatus === "failed" ? "warning" : "muted"}>{formatStatus(task.taskStatus)}</Badge></td>
                <td>
                  <div className="flex gap-2">
                    <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => onView(task)}>查看</Button>
                    <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => onDelete(task)}>删除</Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}


function ChunkDetailDialog({ detail, onClose }: { detail: OntologyChunkDetail; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
      <div className="paper-dialog max-w-6xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold text-ink">chunk 详情</h3>
            <p className="mt-2 text-sm text-slate-600">{detail.chunk.chunkId}</p>
          </div>
          <Button type="button" variant="outline" onClick={onClose}>关闭</Button>
        </div>
        <div className="mt-6 grid gap-5 lg:grid-cols-2">
          <TextBlock title="chunk 原文" value={detail.chunk.chunkText} />
          {detail.layerResults.length > 1 ? (
            detail.layerResults.map((result) => (
              <TextBlock key={result.id} title={`${formatLayerName(result.layerName)} prompt 与输出`} value={`PROMPT:\n${result.finalPrompt || "暂无"}\n\nOUTPUT:\n${result.outputContent || result.errorMessage || "暂无"}\n\nPARSED:\n${JSON.stringify(result.parsedOutput ?? {}, null, 2)}`} />
            ))
          ) : (
            <>
              <TextBlock title="最终 prompt" value={detail.result?.finalPrompt || "暂无"} />
              <TextBlock title="原始模型输出" value={detail.result?.outputContent || detail.result?.errorMessage || "暂无"} />
              <TextBlock title="解析后的结构化结果" value={JSON.stringify(detail.result?.parsedOutput ?? {}, null, 2)} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}


function TextBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white/75 p-4">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <pre className="mt-3 max-h-[520px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 font-mono text-sm leading-7 text-ink">
        {value}
      </pre>
    </div>
  );
}


type ParsedOutput = {
  parsed: unknown | null;
  axioms: Array<Record<string, unknown>>;
  relationCounts: Record<string, number>;
  classCount: number;
  propertyCount: number;
};


function ResultSummary({ task }: { task: OntologyTaskItem }) {
  const parsed = parseOutput(task.outputContent);
  const relationRows = Object.entries(parsed.relationCounts).sort(([left], [right]) => left.localeCompare(right));
  const totalAxioms = parsed.axioms.length;

  return (
    <div className="mt-5 space-y-4">
      <div className="grid gap-3 md:grid-cols-4">
        <StatCard label="学习公理总数" value={String(totalAxioms)} />
        <StatCard label="类数量" value={String(parsed.classCount)} />
        <StatCard label="属性数量" value={String(parsed.propertyCount)} />
        <StatCard label="输出状态" value={formatStatus(task.taskStatus)} />
      </div>
      <div className="rounded-2xl border border-line bg-white/75 p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-500">公理类型统计</p>
          <Badge variant="muted">按 relation 分类</Badge>
        </div>
        {relationRows.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">当前输出中未识别到 axioms 列表或四类公理结构。</p>
        ) : (
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {relationRows.map(([relation, count]) => (
              <div key={relation} className="rounded-xl border border-line bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.18em] text-sageDark/70">{relation}</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{count}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white/75 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.18em] text-sageDark/70">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}


function AxiomTable({ task }: { task: OntologyTaskItem }) {
  const [page, setPage] = useState(1);
  const parsed = parseOutput(task.outputContent);
  const pageSize = 20;
  const totalPages = Math.max(1, Math.ceil(parsed.axioms.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageRows = parsed.axioms.slice((safePage - 1) * pageSize, safePage * pageSize);

  useEffect(() => {
    setPage(1);
  }, [task.id]);

  if (parsed.axioms.length === 0) {
    return null;
  }

  return (
    <div className="mt-5 overflow-hidden rounded-2xl border border-line bg-white/75">
      <div className="border-b border-line px-4 py-3">
        <p className="text-sm font-medium text-slate-500">学习到的公理列表</p>
      </div>
      <div className="overflow-x-auto">
        <table className="paper-table min-w-[980px]">
          <thead>
            <tr>
              <th>#</th>
              <th>subject</th>
              <th>relation</th>
              <th>object</th>
              <th>chunk</th>
              <th>evidence</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((axiom, index) => (
              <tr key={`${String(axiom.subject)}-${String(axiom.relation)}-${safePage}-${index}`}>
                <td>{(safePage - 1) * pageSize + index + 1}</td>
                <td>{formatCell(axiom.subject)}</td>
                <td>{formatCell(axiom.relation)}</td>
                <td>{formatCell(axiom.object)}</td>
                <td>{formatCell(axiom.chunk)}</td>
                <td>
                  <p className="max-w-[360px] truncate">{formatCell(axiom.evidence)}</p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm text-slate-600">
        <span>
          共 {parsed.axioms.length} 条，每页 {pageSize} 条，第 {safePage} / {totalPages} 页
        </span>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            className="px-3 py-2 text-xs"
            disabled={safePage <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            上一页
          </Button>
          <Button
            type="button"
            variant="outline"
            className="px-3 py-2 text-xs"
            disabled={safePage >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
          >
            下一页
          </Button>
        </div>
      </div>
    </div>
  );
}


function parseOutput(output: string): ParsedOutput {
  const parsed = parseJsonLike(output);
  const axioms = extractAxioms(parsed);
  const relationCounts = axioms.reduce<Record<string, number>>((counts, axiom) => {
    const relation = String(axiom.relation ?? axiom.predicate ?? "unknown").trim() || "unknown";
    counts[relation] = (counts[relation] ?? 0) + 1;
    return counts;
  }, {});

  const objectValue = parsed && typeof parsed === "object" && !Array.isArray(parsed)
    ? (parsed as Record<string, unknown>)
    : {};

  return {
    parsed,
    axioms,
    relationCounts,
    classCount: Array.isArray(objectValue.classes) ? objectValue.classes.length : 0,
    propertyCount: Array.isArray(objectValue.properties) ? objectValue.properties.length : 0,
  };
}


function extractAxioms(parsed: unknown): Array<Record<string, unknown>> {
  if (!parsed || typeof parsed !== "object") {
    return [];
  }
  if (Array.isArray(parsed)) {
    return parsed.filter(isRecord);
  }
  const record = parsed as Record<string, unknown>;
  if (Array.isArray(record.axioms)) {
    return record.axioms.filter(isRecord);
  }

  const converted: Array<Record<string, unknown>> = [];
  for (const item of asArray(record.subClassOf)) {
    if (isRecord(item)) {
      converted.push({ subject: item.sub, relation: "rdfs:subClassOf", object: item.super });
    }
  }
  for (const item of asArray(record.subPropertyOf)) {
    if (isRecord(item)) {
      converted.push({ subject: item.sub, relation: "rdfs:subPropertyOf", object: item.super });
    }
  }
  for (const item of asArray(record.domain ?? record.domain_axioms)) {
    if (isRecord(item)) {
      converted.push({ subject: item.property, relation: "rdfs:domain", object: item.class });
    }
  }
  for (const item of asArray(record.range ?? record.range_axioms)) {
    if (isRecord(item)) {
      converted.push({ subject: item.property, relation: "rdfs:range", object: item.class });
    }
  }
  return converted;
}


function formatModelOutput(output: string) {
  const parsed = parseJsonLike(output);
  if (parsed === null) {
    return output || "暂无输出";
  }
  return JSON.stringify(parsed, null, 2);
}


function parseJsonLike(output: string): unknown | null {
  const cleaned = output.trim().replace(/^```[a-zA-Z0-9_-]*\n?/, "").replace(/\n?```$/, "").trim();
  if (!cleaned) {
    return null;
  }
  try {
    return JSON.parse(cleaned);
  } catch {
    const start = cleaned.indexOf("{");
    const end = cleaned.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(cleaned.slice(start, end + 1));
      } catch {
        return null;
      }
    }
    return null;
  }
}


function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}


function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}


function formatCell(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  return String(value);
}


function formatStatus(status: string) {
  if (status === "completed") {
    return "已完成";
  }
  if (status === "partial_success") {
    return "部分完成";
  }
  if (status === "running") {
    return "运行中";
  }
  if (status === "pending") {
    return "等待中";
  }
  if (status === "stopping") {
    return "停止中";
  }
  if (status === "stopped") {
    return "已停止";
  }
  if (status === "failed") {
    return "失败";
  }
  return "未开始";
}


function formatLayerName(layerName: string) {
  if (layerName === "semantic_network") {
    return "第一层：语义网络层";
  }
  if (layerName === "term_refinement") {
    return "第二层：术语精化层";
  }
  if (layerName === "concept_modeling") {
    return "第三层：概念建模层";
  }
  if (layerName === "baseline") {
    return "baseline";
  }
  return layerName || "结果";
}
