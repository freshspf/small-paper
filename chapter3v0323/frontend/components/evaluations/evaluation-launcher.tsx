"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";

import {
  createEvaluationTask,
  type DatasetListItem,
  type EvaluationCreateResult,
  type PromptTemplateItem,
} from "@/lib/api";
import { type ModelItem } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


type EvaluationLauncherProps = {
  models: ModelItem[];
  datasets: DatasetListItem[];
  templates: PromptTemplateItem[];
};


const TEMPLATE_TYPE_LABELS: Record<PromptTemplateItem["templateType"], string> = {
  basic: "基础型",
  instruction_enhanced: "指令增强型",
  context_guided: "上下文引导型",
};


export function EvaluationLauncher({
  models,
  datasets,
  templates,
}: EvaluationLauncherProps) {
  const [selectedModelId, setSelectedModelId] = useState<number>(models[0]?.id ?? 0);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number>(datasets[0]?.id ?? 0);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number>(
    templates.find((item) => item.isDefault)?.id ?? templates[0]?.id ?? 0,
  );
  const [createdTask, setCreatedTask] = useState<EvaluationCreateResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selectedModel = useMemo(
    () => models.find((item) => item.id === selectedModelId),
    [models, selectedModelId],
  );
  const selectedDataset = useMemo(
    () => datasets.find((item) => item.id === selectedDatasetId),
    [datasets, selectedDatasetId],
  );
  const selectedTemplate = useMemo(
    () => templates.find((item) => item.id === selectedTemplateId),
    [templates, selectedTemplateId],
  );

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setCreatedTask(null);

    startTransition(async () => {
      try {
        const result = await createEvaluationTask({
          datasetId: selectedDatasetId,
          modelId: selectedModelId,
          promptTemplateId: selectedTemplateId,
        });
        setCreatedTask(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "启动评测失败，请稍后重试。");
      }
    });
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.62fr_0.38fr]">
      <Card className="overflow-hidden">
        <div className="border-b border-line px-6 py-5">
          <h3 className="text-lg font-semibold text-ink">评测配置</h3>
          <p className="text-sm text-slate-600">选择模型、数据集和提示词模板后，直接启动评测任务。</p>
        </div>

        <form className="space-y-5 p-6" onSubmit={handleSubmit}>
          <label className="space-y-2">
            <span className="text-sm font-medium text-ink">选择模型</span>
            <select
              className="paper-input"
              value={selectedModelId}
              onChange={(event) => setSelectedModelId(Number(event.target.value))}
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} / {model.provider}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-ink">选择数据集</span>
            <select
              className="paper-input"
              value={selectedDatasetId}
              onChange={(event) => setSelectedDatasetId(Number(event.target.value))}
            >
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name} / {dataset.samples} 条
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-ink">选择提示词模板</span>
            <select
              className="paper-input"
              value={selectedTemplateId}
              onChange={(event) => setSelectedTemplateId(Number(event.target.value))}
            >
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name} / {TEMPLATE_TYPE_LABELS[template.templateType]}
                </option>
              ))}
            </select>
          </label>

          {errorMessage ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
              {errorMessage}
            </div>
          ) : null}

          <div className="flex justify-end">
            <Button type="submit" variant="secondary" disabled={isPending}>
              {isPending ? "评测中..." : "开始评测"}
            </Button>
          </div>
        </form>
      </Card>

      <div className="space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-ink">当前配置摘要</h3>
              <p className="text-sm text-slate-600">用于展示本次评测的输入配置。</p>
            </div>
            <Badge>配置预览</Badge>
          </div>

          <div className="mt-5 space-y-4">
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-sm text-slate-500">模型</p>
              <p className="mt-2 text-base font-semibold text-ink">{selectedModel?.name ?? "--"}</p>
            </div>
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-sm text-slate-500">数据集</p>
              <p className="mt-2 text-base font-semibold text-ink">{selectedDataset?.name ?? "--"}</p>
              <p className="mt-1 text-sm text-slate-600">样本数：{selectedDataset?.samples ?? 0}</p>
            </div>
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-sm text-slate-500">提示词模板</p>
              <p className="mt-2 text-base font-semibold text-ink">{selectedTemplate?.name ?? "--"}</p>
              <p className="mt-1 text-sm text-slate-600">
                类型：{selectedTemplate ? TEMPLATE_TYPE_LABELS[selectedTemplate.templateType] : "--"}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-ink">任务状态</h3>
              <p className="text-sm text-slate-600">评测启动后，可直接跳转查看结果详情。</p>
            </div>
            <Badge variant={createdTask ? "success" : "muted"}>
              {createdTask ? "已完成" : "未启动"}
            </Badge>
          </div>

          {createdTask ? (
            <div className="mt-5 space-y-4">
              <div className="rounded-xl border border-line bg-white/70 p-4">
                <p className="text-sm text-slate-500">任务名称</p>
                <p className="mt-2 text-base font-semibold text-ink">{createdTask.taskName}</p>
              </div>
              <div className="rounded-xl border border-line bg-white/70 p-4">
                <p className="text-sm text-slate-500">任务状态</p>
                <p className="mt-2 text-base font-semibold text-ink">{createdTask.status}</p>
                <p className="mt-1 text-sm text-slate-600">生成结果数：{createdTask.resultCount}</p>
              </div>
              <Link
                href={`/evaluations/${createdTask.taskId}`}
                className="inline-flex rounded-xl bg-sage px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-sageDark"
              >
                查看评测结果
              </Link>
            </div>
          ) : (
            <div className="mt-5 rounded-xl border border-dashed border-line bg-white/70 p-5 text-sm text-slate-500">
              完成左侧配置并点击“开始评测”后，系统将在这里显示任务状态与结果入口。
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
