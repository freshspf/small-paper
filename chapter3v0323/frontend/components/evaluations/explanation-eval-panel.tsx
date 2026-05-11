"use client";

import { useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getExplanationEvalRecords,
  getExplanationEvalStats,
  saveExplanationEvalRecord,
  type ExplanationEvalItem,
  type ExplanationEvalPage,
  type ExplanationEvalStats,
} from "@/lib/api";


type ExplanationEvalPanelProps = {
  taskId: number;
  initialStats: ExplanationEvalStats;
  initialPage: ExplanationEvalPage;
};

type AnnotationForm = {
  explanationCorrectLabel: string;
  hallucinationLabel: string;
  annotationRemark: string;
};


export function ExplanationEvalPanel({ taskId, initialStats, initialPage }: ExplanationEvalPanelProps) {
  const [stats, setStats] = useState(initialStats);
  const [pageData, setPageData] = useState(initialPage);
  const [annotationStatus, setAnnotationStatus] = useState("");
  const [selected, setSelected] = useState<ExplanationEvalItem | null>(null);
  const [formState, setFormState] = useState<AnnotationForm>({
    explanationCorrectLabel: "",
    hallucinationLabel: "",
    annotationRemark: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function openDialog(item: ExplanationEvalItem) {
    setSelected(item);
    setFormState({
      explanationCorrectLabel: item.annotation.explanationCorrectLabel === null ? "" : String(item.annotation.explanationCorrectLabel),
      hallucinationLabel: item.annotation.hallucinationLabel === null ? "" : String(item.annotation.hallucinationLabel),
      annotationRemark: item.annotation.annotationRemark,
    });
    setMessage(null);
    setErrorMessage(null);
  }

  function loadPage(nextPage: number, nextStatus = annotationStatus) {
    startTransition(async () => {
      try {
        const [nextPageData, nextStats] = await Promise.all([
          getExplanationEvalRecords({
            taskId,
            page: nextPage,
            pageSize: pageData.pageSize,
            annotationStatus: nextStatus,
          }),
          getExplanationEvalStats(taskId),
        ]);
        setPageData(nextPageData);
        setStats(nextStats);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取解释能力评估数据失败。");
      }
    });
  }

  function handleStatusChange(value: string) {
    setAnnotationStatus(value);
    loadPage(1, value);
  }

  function saveAnnotation() {
    if (!selected) {
      return;
    }
    if (formState.explanationCorrectLabel === "" || formState.hallucinationLabel === "") {
      setErrorMessage("请同时选择解释是否正确、是否存在幻觉。");
      return;
    }

    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        await saveExplanationEvalRecord({
          taskId,
          resultId: selected.resultId,
          explanationCorrectLabel: Number(formState.explanationCorrectLabel),
          hallucinationLabel: Number(formState.hallucinationLabel),
          annotationRemark: formState.annotationRemark || null,
        });
        const [nextPageData, nextStats] = await Promise.all([
          getExplanationEvalRecords({
            taskId,
            page: pageData.page,
            pageSize: pageData.pageSize,
            annotationStatus,
          }),
          getExplanationEvalStats(taskId),
        ]);
        setPageData(nextPageData);
        setStats(nextStats);
        setSelected(null);
        setMessage("解释标注已保存。");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "保存解释标注失败。");
      }
    });
  }

  const maxPage = Math.max(Math.ceil(pageData.total / pageData.pageSize), 1);

  return (
    <>
      <Card className="overflow-hidden">
        <div className="border-b border-line px-6 py-5">
          <h3 className="text-lg font-semibold text-ink">解释能力评估</h3>
          <p className="text-sm text-slate-600">
            仅对判断正确且执行成功的样本进行解释文本标注，并统计解释正确率与幻觉率。
          </p>
        </div>

        <div className="grid gap-4 border-b border-line bg-white/40 px-6 py-5 md:grid-cols-3 xl:grid-cols-6">
          <Metric label="判断正确样本数" value={stats.correctCaseCount} />
          <Metric label="已标注样本数" value={stats.annotatedCount} />
          <Metric label="解释正确数" value={stats.explanationCorrectCount} />
          <Metric label="幻觉样本数" value={stats.hallucinationCount} />
          <Metric label="解释正确率" value={stats.explanationAccuracy.toFixed(3)} />
          <Metric label="幻觉率" value={stats.hallucinationRate.toFixed(3)} />
        </div>

        <div className="flex flex-col gap-3 border-b border-line px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="text-sm text-slate-500">共 {pageData.total} 条可标注解释</div>
          <div className="flex gap-3">
            <select className="paper-input w-44" value={annotationStatus} onChange={(event) => handleStatusChange(event.target.value)}>
              <option value="">全部标注状态</option>
              <option value="pending">未标注</option>
              <option value="completed">已标注</option>
            </select>
            <Button variant="outline" disabled={isPending} onClick={() => loadPage(pageData.page)}>
              刷新
            </Button>
          </div>
        </div>

        {message ? <div className="border-b border-line bg-emerald-50 px-6 py-3 text-sm text-emerald-700">{message}</div> : null}
        {errorMessage ? <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

        <div className="overflow-x-auto">
          <table className="paper-table min-w-[1180px]">
            <thead>
              <tr>
                <th>编号</th>
                <th>公理类型</th>
                <th>公理文本</th>
                <th>真实标签</th>
                <th>预测标签</th>
                <th>explanation 摘要</th>
                <th>标注状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pageData.records.map((item) => (
                <tr key={item.resultId}>
                  <td>{item.resultId}</td>
                  <td>{item.axiomType || "--"}</td>
                  <td className="max-w-[320px] truncate" title={item.axiomText}>{item.axiomText || "--"}</td>
                  <td><LabelBadge value={item.trueLabel} /></td>
                  <td><LabelBadge value={item.predictLabel} /></td>
                  <td className="max-w-[360px] truncate" title={item.explanation}>{item.explanation || "--"}</td>
                  <td><AnnotationStatusBadge status={item.annotation.annotationStatus} /></td>
                  <td>
                    <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => openDialog(item)}>
                      {item.annotation.annotationStatus === "completed" ? "查看/修改" : "标注"}
                    </Button>
                  </td>
                </tr>
              ))}
              {pageData.records.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center text-slate-500">暂无可标注解释</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-line px-6 py-4 text-sm text-slate-600">
          <span>第 {pageData.page} / {maxPage} 页</span>
          <div className="flex gap-2">
            <Button variant="outline" disabled={isPending || pageData.page <= 1} onClick={() => loadPage(pageData.page - 1)}>上一页</Button>
            <Button variant="outline" disabled={isPending || pageData.page >= maxPage} onClick={() => loadPage(pageData.page + 1)}>下一页</Button>
          </div>
        </div>
      </Card>

      {selected ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-5xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">解释能力人工标注</h3>
                <p className="mt-2 text-sm text-slate-600">标注解释是否语义正确、逻辑合理，以及是否包含无依据推断。</p>
              </div>
              <Button variant="outline" onClick={() => setSelected(null)}>关闭</Button>
            </div>

            <div className="mt-6 grid gap-4">
              <DetailBlock label="公理文本" value={selected.axiomText || "--"} />
              <DetailBlock label="explanation" value={selected.explanation || "--"} />
              <DetailBlock label="rawOutput" value={selected.rawOutput || "--"} />
            </div>

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <RadioGroup
                label="解释是否正确"
                value={formState.explanationCorrectLabel}
                onChange={(value) => setFormState((current) => ({ ...current, explanationCorrectLabel: value }))}
                options={[["1", "正确"], ["0", "错误 / 语义不一致"]]}
              />
              <RadioGroup
                label="是否存在幻觉"
                value={formState.hallucinationLabel}
                onChange={(value) => setFormState((current) => ({ ...current, hallucinationLabel: value }))}
                options={[["0", "不存在幻觉"], ["1", "存在幻觉"]]}
              />
            </div>

            <label className="mt-5 block space-y-2">
              <span className="text-sm font-medium text-ink">标注备注</span>
              <textarea
                className="paper-textarea"
                value={formState.annotationRemark}
                onChange={(event) => setFormState((current) => ({ ...current, annotationRemark: event.target.value }))}
                placeholder="可记录判断依据、错误类型或幻觉来源"
              />
            </label>

            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelected(null)}>取消</Button>
              <Button variant="secondary" disabled={isPending} onClick={saveAnnotation}>
                保存标注
              </Button>
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
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
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


function AnnotationStatusBadge({ status }: { status: string }) {
  return <Badge variant={status === "completed" ? "success" : "muted"}>{status === "completed" ? "已标注" : "未标注"}</Badge>;
}


function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap rounded-2xl border border-line bg-mist/55 p-4 text-sm leading-7 text-slate-700">
        {value}
      </pre>
    </div>
  );
}


function RadioGroup({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      <div className="mt-3 flex flex-wrap gap-3">
        {options.map(([optionValue, optionLabel]) => (
          <label key={optionValue} className="inline-flex items-center gap-2 rounded-xl border border-line bg-white/80 px-4 py-2 text-sm text-ink">
            <input
              type="radio"
              checked={value === optionValue}
              onChange={() => onChange(optionValue)}
            />
            {optionLabel}
          </label>
        ))}
      </div>
    </div>
  );
}
