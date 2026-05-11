"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  createEvalTask,
  deleteEvalTask,
  getEvalTasks,
  startEvalTask,
  stopEvalTask,
  type EvalDatasetListItem,
  type EvalTaskItem,
} from "@/lib/api";
import { type ModelConfigItem, type PromptTemplateConfigItem } from "@/lib/mock-data";


type JobsTableProps = {
  jobs: EvalTaskItem[];
  datasets: EvalDatasetListItem[];
  models: ModelConfigItem[];
  prompts: PromptTemplateConfigItem[];
};

type FormState = {
  taskName: string;
  datasetId: string;
  modelId: string;
  promptId: string;
  remark: string;
};

const EMPTY_FORM: FormState = {
  taskName: "",
  datasetId: "",
  modelId: "",
  promptId: "",
  remark: "",
};


export function JobsTable({ jobs, datasets, models, prompts }: JobsTableProps) {
  const [items, setItems] = useState(jobs);
  const [filters, setFilters] = useState({ taskName: "", taskStatus: "" });
  const [formState, setFormState] = useState<FormState>(EMPTY_FORM);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const completedCount = useMemo(
    () => items.filter((item) => item.taskStatus === "success" || item.taskStatus === "completed").length,
    [items],
  );
  const runningCount = useMemo(
    () => items.filter((item) => item.taskStatus === "running" || item.taskStatus === "stopping").length,
    [items],
  );

  useEffect(() => {
    const hasRunningTask = items.some((item) => item.taskStatus === "running" || item.taskStatus === "stopping");
    if (!hasRunningTask) {
      return;
    }

    const timer = window.setInterval(async () => {
      try {
        const result = await getEvalTasks(filters);
        setItems(result);
      } catch {
        // Keep the current table visible if a transient refresh fails.
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [filters, items]);

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setFormState((current) => ({ ...current, [key]: value }));
  }

  function closeDialog() {
    setIsDialogOpen(false);
    setFormState(EMPTY_FORM);
    setErrorMessage(null);
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getEvalTasks(filters);
        setItems(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "查询失败，请稍后重试。");
      }
    });
  }

  function resetFilters() {
    const nextFilters = { taskName: "", taskStatus: "" };
    setFilters(nextFilters);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getEvalTasks(nextFilters);
        setItems(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "查询失败，请稍后重试。");
      }
    });
  }

  function validateForm() {
    if (!formState.taskName || !formState.datasetId || !formState.modelId || !formState.promptId) {
      setErrorMessage("请填写任务名称，并选择数据集、模型和提示词模板。");
      return false;
    }
    return true;
  }

  async function createTaskOnly() {
    setMessage(null);
    setErrorMessage(null);
    if (!validateForm()) {
      return;
    }

    startTransition(async () => {
      try {
        const created = await createEvalTask({
          taskName: formState.taskName,
          datasetId: Number(formState.datasetId),
          modelId: Number(formState.modelId),
          promptId: Number(formState.promptId),
          remark: formState.remark || null,
        });
        setItems((current) => [created, ...current]);
        setMessage(`评估任务“${created.taskName}”已创建，状态为未评估。`);
        closeDialog();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "创建任务失败，请稍后重试。");
      }
    });
  }

  async function createAndStartTask() {
    setMessage(null);
    setErrorMessage(null);
    if (!validateForm()) {
      return;
    }

    startTransition(async () => {
      try {
        const created = await createEvalTask({
          taskName: formState.taskName,
          datasetId: Number(formState.datasetId),
          modelId: Number(formState.modelId),
          promptId: Number(formState.promptId),
          remark: formState.remark || null,
        });
        const started = await startEvalTask(created.id);
        setItems((current) => [started, ...current]);
        setMessage(`评估任务“${started.taskName}”已开始，后台正在评估。`);
        closeDialog();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "启动任务失败，请稍后重试。");
      }
    });
  }

  function handleStart(task: EvalTaskItem) {
    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const started = await startEvalTask(task.id);
        setItems((current) => current.map((item) => (item.id === task.id ? started : item)));
        setMessage(`评估任务“${started.taskName}”已开始，后台正在评估。`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "启动任务失败，请稍后重试。");
      }
    });
  }

  function handleStop(task: EvalTaskItem) {
    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const stopped = await stopEvalTask(task.id);
        setItems((current) => current.map((item) => (item.id === task.id ? stopped : item)));
        setMessage(`已请求停止评估任务：${stopped.taskName}`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "停止任务失败，请稍后重试。");
      }
    });
  }

  function handleDelete(task: EvalTaskItem) {
    const confirmed = window.confirm(`确认删除评估任务“${task.taskName}”及其结果记录吗？`);
    if (!confirmed) {
      return;
    }
    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        await deleteEvalTask(task.id);
        setItems((current) => current.filter((item) => item.id !== task.id));
        setMessage(`已删除评估任务：${task.taskName}`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "删除失败，请稍后重试。");
      }
    });
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">任务总数</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{items.length}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">已完成任务</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{completedCount}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">评估中任务</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{runningCount}</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-line px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">评估任务列表</h3>
            <p className="text-sm text-slate-600">支持先创建任务，再按需启动后台评估。</p>
          </div>
          <Button variant="secondary" onClick={() => setIsDialogOpen(true)}>
            新建评估任务
          </Button>
        </div>

        <form className="grid gap-3 border-b border-line bg-white/40 px-6 py-4 lg:grid-cols-[1fr_0.7fr_auto_auto]" onSubmit={handleSearch}>
          <input
            className="paper-input"
            value={filters.taskName}
            onChange={(event) => setFilters((current) => ({ ...current, taskName: event.target.value }))}
            placeholder="按任务名称搜索"
          />
          <select
            className="paper-input"
            value={filters.taskStatus}
            onChange={(event) => setFilters((current) => ({ ...current, taskStatus: event.target.value }))}
          >
            <option value="">全部状态</option>
            <option value="pending">未评估</option>
            <option value="running">评估中</option>
            <option value="stopping">停止中</option>
            <option value="stopped">已停止</option>
            <option value="success">评估完成</option>
            <option value="completed">部分完成</option>
            <option value="failed">失败</option>
          </select>
          <Button type="submit" variant="secondary" disabled={isPending}>查询</Button>
          <Button type="button" variant="outline" onClick={resetFilters} disabled={isPending}>重置</Button>
        </form>

        {message ? <div className="border-b border-line bg-emerald-50 px-6 py-3 text-sm text-emerald-700">{message}</div> : null}
        {errorMessage ? <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

        <div className="overflow-x-auto">
          <table className="paper-table min-w-[1180px]">
            <thead>
              <tr>
                <th>编号</th>
                <th>任务名称</th>
                <th>数据集</th>
                <th>模型</th>
                <th>提示词模板</th>
                <th>状态</th>
                <th>总样本</th>
                <th>成功</th>
                <th>失败</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map((task) => (
                <tr key={task.id}>
                  <td>{task.id}</td>
                  <td className="font-medium text-ink">{task.taskName}</td>
                  <td>{task.datasetName}</td>
                  <td>{task.modelName}</td>
                  <td>{task.promptName}</td>
                  <td>
                    <TaskProgress task={task} />
                  </td>
                  <td>{task.totalCount}</td>
                  <td>{task.successCount}</td>
                  <td>{task.failCount}</td>
                  <td>{task.createdTime}</td>
                  <td>
                    <div className="flex gap-2">
                      <Link href={`/evaluations/${task.id}`} className="inline-flex items-center justify-center rounded-xl border border-line bg-white/88 px-3 py-2 text-xs font-medium text-ink shadow-sm transition-all hover:bg-mist">
                        查看详情
                      </Link>
                      <Button
                        variant="secondary"
                        className="px-3 py-2 text-xs"
                        disabled={isPending || task.taskStatus === "running" || task.taskStatus === "stopping"}
                        onClick={() => handleStart(task)}
                      >
                        {task.taskStatus === "pending" ? "开始评估" : "重新评估"}
                      </Button>
                      {(task.taskStatus === "running" || task.taskStatus === "stopping") ? (
                        <Button
                          variant="outline"
                          className="px-3 py-2 text-xs"
                          disabled={isPending || task.taskStatus === "stopping"}
                          onClick={() => handleStop(task)}
                        >
                          {task.taskStatus === "stopping" ? "停止中" : "停止评估"}
                        </Button>
                      ) : null}
                      <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => handleDelete(task)}>
                        删除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {isDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-3xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">创建评估任务</h3>
              </div>
              <Button variant="outline" onClick={closeDialog}>关闭</Button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={(event) => event.preventDefault()}>
              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">任务名称</span>
                <input className="paper-input" value={formState.taskName} onChange={(event) => updateForm("taskName", event.target.value)} required />
              </label>
              <div className="grid gap-5 md:grid-cols-3">
                <SelectField label="选择数据集" value={formState.datasetId} onChange={(value) => updateForm("datasetId", value)} options={datasets.map((item) => ({ value: String(item.id), label: `${item.datasetName}（${item.recordCount}）` }))} />
                <SelectField label="选择模型" value={formState.modelId} onChange={(value) => updateForm("modelId", value)} options={models.filter((item) => item.status === 1).map((item) => ({ value: String(item.id), label: item.modelName }))} />
                <SelectField label="选择提示词" value={formState.promptId} onChange={(value) => updateForm("promptId", value)} options={prompts.filter((item) => item.status === 1).map((item) => ({ value: String(item.id), label: item.templateName }))} />
              </div>
              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">任务备注</span>
                <textarea className="paper-textarea" value={formState.remark} onChange={(event) => updateForm("remark", event.target.value)} />
              </label>
              {errorMessage ? <p className="text-sm text-amber-700">{errorMessage}</p> : null}
              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={closeDialog}>取消</Button>
                <Button type="button" variant="outline" disabled={isPending} onClick={createTaskOnly}>
                  创建
                </Button>
                <Button type="button" variant="secondary" disabled={isPending} onClick={createAndStartTask}>
                  {isPending ? "处理中..." : "开始评估"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}


function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<{ value: string; label: string }> }) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-medium text-ink">{label}</span>
      <select className="paper-input" value={value} onChange={(event) => onChange(event.target.value)} required>
        <option value="">请选择</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}


function StatusBadge({ status }: { status: string }) {
  const labelMap: Record<string, string> = {
    pending: "未评估",
    running: "评估中",
    stopping: "停止中",
    stopped: "已停止",
    success: "评估完成",
    completed: "部分完成",
    failed: "失败",
  };
  const variant = status === "success" || status === "completed" ? "success" : status === "failed" || status === "stopped" ? "warning" : "muted";
  return <Badge variant={variant}>{labelMap[status] ?? status}</Badge>;
}


function TaskProgress({ task }: { task: EvalTaskItem }) {
  const finished = task.successCount + task.failCount;
  const total = task.totalCount || 0;
  const percent = total > 0 ? Math.min(Math.round((finished / total) * 100), 100) : 0;
  const isRunning = task.taskStatus === "running" || task.taskStatus === "stopping";

  return (
    <div className="min-w-[170px] space-y-2">
      <div className="flex items-center justify-between gap-3">
        <StatusBadge status={task.taskStatus} />
        {isRunning ? <span className="text-xs font-medium text-slate-600">正在评估</span> : null}
      </div>
      {isRunning ? (
        <div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${percent}%` }} />
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {finished}/{total}，{percent}%
          </div>
        </div>
      ) : null}
    </div>
  );
}
