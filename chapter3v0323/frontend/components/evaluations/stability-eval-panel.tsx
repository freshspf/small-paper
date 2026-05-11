"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  createStabilityEvalTask,
  getStabilityEvalRecords,
  getStabilityEvalTasks,
  stopStabilityEvalTask,
  type StabilityEvalRecordItem,
  type StabilityEvalRecordPage,
  type StabilityEvalTaskItem,
  type StabilityTemplateMap,
} from "@/lib/api";


type StabilityEvalPanelProps = {
  baseTaskId: number;
  templates: StabilityTemplateMap;
  initialTasks: StabilityEvalTaskItem[];
  initialRecordPage: StabilityEvalRecordPage;
};


export function StabilityEvalPanel({ baseTaskId, templates, initialTasks, initialRecordPage }: StabilityEvalPanelProps) {
  const [tasks, setTasks] = useState(initialTasks);
  const [recordPage, setRecordPage] = useState(initialRecordPage);
  const [selectedRecord, setSelectedRecord] = useState<StabilityEvalRecordItem | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const currentTask = useMemo(() => tasks[0] ?? null, [tasks]);
  const maxPage = Math.max(Math.ceil(recordPage.total / recordPage.pageSize), 1);
  const isRunning = currentTask?.taskStatus === "running" || currentTask?.taskStatus === "stopping";
  const finishedCount = (currentTask?.successCount ?? 0) + (currentTask?.failCount ?? 0);
  const progressPercent = currentTask?.totalCount ? Math.min(Math.round((finishedCount / currentTask.totalCount) * 100), 100) : 0;

  useEffect(() => {
    if (!isRunning || !currentTask) {
      return;
    }
    const timer = window.setInterval(() => {
      refresh(currentTask.id, recordPage.page);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [isRunning, currentTask?.id, recordPage.page]);

  function refresh(stabilityTaskId = currentTask?.id, page = recordPage.page) {
    startTransition(async () => {
      try {
        const nextTasks = await getStabilityEvalTasks(baseTaskId);
        setTasks(nextTasks);
        const targetTaskId = stabilityTaskId ?? nextTasks[0]?.id;
        if (targetTaskId) {
          const nextRecords = await getStabilityEvalRecords({
            stabilityTaskId: targetTaskId,
            page,
            pageSize: recordPage.pageSize,
          });
          setRecordPage(nextRecords);
        }
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "刷新稳定性评估失败。");
      }
    });
  }

  function startEvaluation() {
    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const task = await createStabilityEvalTask(baseTaskId);
        setTasks((current) => [task, ...current]);
        setRecordPage({ records: [], total: 0, page: 1, pageSize: recordPage.pageSize });
        setMessage("稳定性评估任务已开始，后台正在执行。");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "启动稳定性评估失败。");
      }
    });
  }

  function stopEvaluation() {
    if (!currentTask) {
      return;
    }
    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const stopped = await stopStabilityEvalTask(currentTask.id);
        setTasks((current) => current.map((task) => (task.id === stopped.id ? stopped : task)));
        setMessage("已请求停止稳定性评估，当前模型请求结束后会停止后续扰动样本。");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "停止稳定性评估失败。");
      }
    });
  }

  return (
    <>
      <Card className="overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-line px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">稳定性评估</h3>
            <p className="text-sm text-slate-600">基于四类公理的语义等价扰动，统计硬一致性和软一致性。</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" disabled={isPending} onClick={() => refresh()}>
              刷新
            </Button>
            {isRunning ? (
              <Button
                variant="outline"
                disabled={isPending || currentTask?.taskStatus === "stopping"}
                onClick={stopEvaluation}
              >
                {currentTask?.taskStatus === "stopping" ? "停止中" : "停止评估"}
              </Button>
            ) : null}
            <Button variant="secondary" disabled={isPending} onClick={startEvaluation}>
              开始稳定性评估
            </Button>
          </div>
        </div>

        <div className="grid gap-4 border-b border-line bg-white/40 px-6 py-5 md:grid-cols-2 xl:grid-cols-4">
          {Object.entries(templates).map(([axiomType, templateItems]) => (
            <div key={axiomType} className="rounded-2xl border border-line bg-white/80 p-4">
              <p className="font-semibold text-ink">{axiomType}</p>
              <ol className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                {templateItems.map((template) => (
                  <li key={template.templateId}>{template.templateId}. {template.templateText}</li>
                ))}
              </ol>
            </div>
          ))}
        </div>

        <div className="grid gap-4 border-b border-line px-6 py-5 md:grid-cols-3 xl:grid-cols-6">
          <Metric label="总扰动样本数" value={currentTask?.totalCount ?? 0} />
          <Metric label="成功数" value={currentTask?.successCount ?? 0} />
          <Metric label="失败数" value={currentTask?.failCount ?? 0} />
          <Metric label="任务状态" value={formatStatus(currentTask?.taskStatus ?? "未开始")} />
          <Metric label="硬一致性" value={formatMetric(currentTask?.hardConsistency)} />
          <Metric label="软一致性" value={formatMetric(currentTask?.softConsistency)} />
        </div>

        {isRunning ? (
          <div className="border-b border-line bg-emerald-50/45 px-6 py-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-sm font-medium text-ink">正在执行稳定性评估</p>
                <p className="text-xs text-slate-600">
                  已处理 {finishedCount}/{currentTask?.totalCount ?? 0} 个扰动样本，{progressPercent}%
                </p>
              </div>
              <Badge variant="muted">{formatStatus(currentTask?.taskStatus ?? "")}</Badge>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200">
              <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>
        ) : null}

        {message ? <div className="border-b border-line bg-emerald-50 px-6 py-3 text-sm text-emerald-700">{message}</div> : null}
        {errorMessage ? <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

        <div className="overflow-x-auto">
          <table className="paper-table min-w-[1220px]">
            <thead>
              <tr>
                <th>原始样本编号</th>
                <th>模板编号</th>
                <th>扰动样本编号</th>
                <th>公理类型</th>
                <th>扰动文本</th>
                <th>原始预测</th>
                <th>扰动预测</th>
                <th>是否一致</th>
                <th>执行状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {recordPage.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.originalId}</td>
                  <td>{record.templateId}</td>
                  <td>{record.variantId}</td>
                  <td>{record.axiomType}</td>
                  <td className="max-w-[360px] truncate" title={record.perturbedText}>{record.perturbedText}</td>
                  <td><LabelBadge value={record.originalPredictLabel} /></td>
                  <td><LabelBadge value={record.perturbedPredictLabel} /></td>
                  <td><ConsistencyBadge value={record.consistencyFlag} /></td>
                  <td><Badge variant={record.runStatus === "success" ? "success" : "warning"}>{record.runStatus}</Badge></td>
                  <td>
                    <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => setSelectedRecord(record)}>
                      查看详情
                    </Button>
                  </td>
                </tr>
              ))}
              {recordPage.records.length === 0 ? (
                <tr>
                  <td colSpan={10} className="text-center text-slate-500">暂无稳定性评估结果</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-line px-6 py-4 text-sm text-slate-600">
          <span>第 {recordPage.page} / {maxPage} 页</span>
          <div className="flex gap-2">
            <Button variant="outline" disabled={isPending || recordPage.page <= 1 || !currentTask} onClick={() => currentTask && refresh(currentTask.id, recordPage.page - 1)}>上一页</Button>
            <Button variant="outline" disabled={isPending || recordPage.page >= maxPage || !currentTask} onClick={() => currentTask && refresh(currentTask.id, recordPage.page + 1)}>下一页</Button>
          </div>
        </div>
      </Card>

      {selectedRecord ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-4xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">稳定性评估详情</h3>
                <p className="mt-2 text-sm text-slate-600">查看原始表达、扰动表达、上下文与错误信息。</p>
              </div>
              <Button variant="outline" onClick={() => setSelectedRecord(null)}>关闭</Button>
            </div>
            <div className="mt-6 grid gap-4">
              <DetailBlock label="原始表达" value={selectedRecord.originalText || "--"} />
              <DetailBlock label="扰动表达" value={selectedRecord.perturbedText || "--"} />
              <DetailBlock label="上下文信息" value={selectedRecord.contextInfo || "--"} />
              <DetailBlock label="错误信息" value={selectedRecord.errorMessage || "--"} />
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}


function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-line bg-white/80 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}


function LabelBadge({ value }: { value: number | null }) {
  if (value === 1) {
    return <Badge variant="success">正确</Badge>;
  }
  if (value === 0) {
    return <Badge variant="warning">错误</Badge>;
  }
  return <Badge variant="muted">未解析</Badge>;
}


function ConsistencyBadge({ value }: { value: number | null }) {
  if (value === 1) {
    return <Badge variant="success">一致</Badge>;
  }
  if (value === 0) {
    return <Badge variant="warning">不一致</Badge>;
  }
  return <Badge variant="muted">未完成</Badge>;
}


function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap rounded-2xl border border-line bg-mist/55 p-4 text-sm leading-7 text-slate-700">
        {value}
      </pre>
    </div>
  );
}


function formatMetric(value: number | null | undefined) {
  return typeof value === "number" ? value.toFixed(4) : "--";
}


function formatStatus(status: string) {
  const map: Record<string, string> = {
    running: "评估中",
    stopping: "停止中",
    stopped: "已停止",
    success: "已完成",
    completed: "部分完成",
    failed: "失败",
    未开始: "未开始",
  };
  return map[status] ?? status;
}
