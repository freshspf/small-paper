"use client";

import { useState, useTransition } from "react";

import {
  getAnnotationResults,
  getExplanationStats,
  submitAnnotation,
  type AnnotationItemData,
  type EvaluationListItem,
  type ExplanationStatsData,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


type AnnotationWorkspaceProps = {
  tasks: EvaluationListItem[];
  initialTaskId: string;
  initialItems: AnnotationItemData[];
  initialStats: ExplanationStatsData;
};


const LABEL_BUTTONS: Array<{
  label: "correct" | "wrong" | "hallucination";
  text: string;
  variant: "primary" | "secondary" | "outline";
}> = [
  { label: "correct", text: "标记为 correct", variant: "primary" },
  { label: "wrong", text: "标记为 wrong", variant: "secondary" },
  { label: "hallucination", text: "标记为 hallucination", variant: "outline" },
];


function getLabelText(label: AnnotationItemData["explanationLabel"]) {
  if (label === "correct") {
    return "correct";
  }
  if (label === "wrong") {
    return "wrong";
  }
  if (label === "hallucination") {
    return "hallucination";
  }
  return "未标注";
}


export function AnnotationWorkspace({
  tasks,
  initialTaskId,
  initialItems,
  initialStats,
}: AnnotationWorkspaceProps) {
  const [selectedTaskId, setSelectedTaskId] = useState(initialTaskId);
  const [items, setItems] = useState(initialItems);
  const [stats, setStats] = useState(initialStats);
  const [reasonDrafts, setReasonDrafts] = useState<Record<number, string>>(
    Object.fromEntries(initialItems.map((item) => [item.evaluationResultId, item.annotationReason])),
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleTaskChange(taskId: string) {
    setSelectedTaskId(taskId);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const [nextItems, nextStats] = await Promise.all([
          getAnnotationResults(taskId),
          getExplanationStats(),
        ]);
        setItems(nextItems);
        setStats(nextStats);
        setReasonDrafts(
          Object.fromEntries(nextItems.map((item) => [item.evaluationResultId, item.annotationReason])),
        );
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取标注数据失败。");
      }
    });
  }

  function handleReasonChange(evaluationResultId: number, value: string) {
    setReasonDrafts((current) => ({
      ...current,
      [evaluationResultId]: value,
    }));
  }

  function handleAnnotate(
    evaluationResultId: number,
    explanationLabel: "correct" | "wrong" | "hallucination",
  ) {
    setErrorMessage(null);
    startTransition(async () => {
      try {
        await submitAnnotation({
          evaluationResultId,
          explanationLabel,
          annotationReason: reasonDrafts[evaluationResultId] ?? "",
        });

        const [nextItems, nextStats] = await Promise.all([
          getAnnotationResults(selectedTaskId),
          getExplanationStats(),
        ]);
        setItems(nextItems);
        setStats(nextStats);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "提交标注失败。");
      }
    });
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-end justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-ink">评测任务选择</h3>
            <p className="mt-1 text-sm text-slate-600">选择某次评测任务后，对其中每条解释进行人工标注。</p>
          </div>
          <div className="min-w-[320px]">
            <select
              className="paper-input"
              value={selectedTaskId}
              onChange={(event) => handleTaskChange(event.target.value)}
            >
              {tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {task.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {errorMessage ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[0.72fr_0.28fr]">
        <div className="space-y-6">
          {items.map((item) => (
            <Card key={item.evaluationResultId} className="p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-500">样本编号</p>
                  <p className="mt-1 text-base font-semibold text-ink">{item.sampleId}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge>{item.axiomType}</Badge>
                  <Badge variant={item.explanationLabel ? "success" : "muted"}>
                    {getLabelText(item.explanationLabel)}
                  </Badge>
                </div>
              </div>

              <div className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
                <div className="space-y-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
                      Axiom Text
                    </p>
                    <div className="mt-2 rounded-xl bg-white/75 p-4 text-sm leading-7 text-ink">
                      {item.axiomText}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
                      Judgment Result
                    </p>
                    <div className="mt-2 rounded-xl bg-white/75 p-4 text-sm leading-7 text-ink">
                      {item.judgmentResult}
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
                    Explanation
                  </p>
                  <div className="mt-2 rounded-xl bg-white/75 p-4 text-sm leading-7 text-ink">
                    {item.explanation}
                  </div>
                </div>
              </div>

              <div className="mt-5">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
                  Annotation Reason
                </p>
                <textarea
                  className="paper-textarea mt-2 min-h-24"
                  value={reasonDrafts[item.evaluationResultId] ?? ""}
                  onChange={(event) => handleReasonChange(item.evaluationResultId, event.target.value)}
                  placeholder="填写人工标注理由（可选）"
                />
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                {LABEL_BUTTONS.map((button) => (
                  <Button
                    key={button.label}
                    variant={button.variant}
                    disabled={isPending}
                    onClick={() => handleAnnotate(item.evaluationResultId, button.label)}
                  >
                    {button.text}
                  </Button>
                ))}
              </div>
            </Card>
          ))}
        </div>

        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-ink">整体标注统计</h3>
            <div className="mt-5 space-y-4">
              <div className="rounded-xl border border-line bg-white/70 p-4">
                <p className="text-sm text-slate-500">总标注数</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{stats.overall.totalAnnotations}</p>
              </div>
              <div className="rounded-xl border border-line bg-white/70 p-4">
                <p className="text-sm text-slate-500">解释正确率</p>
                <p className="mt-2 text-2xl font-semibold text-ink">
                  {(stats.overall.explanationAccuracy * 100).toFixed(1)}%
                </p>
              </div>
              <div className="rounded-xl border border-line bg-white/70 p-4">
                <p className="text-sm text-slate-500">幻觉率</p>
                <p className="mt-2 text-2xl font-semibold text-ink">
                  {(stats.overall.hallucinationRate * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-ink">按模型统计</h3>
            <div className="mt-5 space-y-4">
              {stats.byModel.map((item) => (
                <div key={item.model} className="rounded-xl border border-line bg-white/70 p-4">
                  <p className="font-medium text-ink">{item.model}</p>
                  <p className="mt-2 text-sm text-slate-600">
                    正确率 {(item.explanationAccuracy * 100).toFixed(1)}% / 幻觉率{" "}
                    {(item.hallucinationRate * 100).toFixed(1)}%
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
