"use client";

import { useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getEvalTaskResults,
  type EvalTaskResultItem,
  type EvalTaskResultPage,
} from "@/lib/api";


type ResultFilters = {
  axiomType: string;
  trueLabel: string;
  predictLabel: string;
  runStatus: string;
};

type EvalTaskResultsTableProps = {
  taskId: number;
  initialPage: EvalTaskResultPage;
};

const EMPTY_FILTERS: ResultFilters = {
  axiomType: "",
  trueLabel: "",
  predictLabel: "",
  runStatus: "",
};


export function EvalTaskResultsTable({ taskId, initialPage }: EvalTaskResultsTableProps) {
  const [pageData, setPageData] = useState(initialPage);
  const [filters, setFilters] = useState<ResultFilters>(EMPTY_FILTERS);
  const [selected, setSelected] = useState<EvalTaskResultItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function updateFilter<K extends keyof ResultFilters>(key: K, value: ResultFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function loadPage(nextPage: number, nextFilters = filters) {
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getEvalTaskResults({
          taskId,
          page: nextPage,
          pageSize: pageData.pageSize,
          ...nextFilters,
        });
        setPageData(result);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取评估结果失败。");
      }
    });
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadPage(1);
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS);
    loadPage(1, EMPTY_FILTERS);
  }

  const maxPage = Math.max(Math.ceil(pageData.total / pageData.pageSize), 1);

  return (
    <>
      <Card className="overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-line px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">样本级评估结果</h3>
            <p className="text-sm text-slate-600">支持按公理类型、标签与执行状态筛选，详情中保留模型原始输出。</p>
          </div>
          <div className="text-sm text-slate-500">共 {pageData.total} 条</div>
        </div>

        <form className="grid gap-3 border-b border-line bg-white/40 px-6 py-4 lg:grid-cols-[1fr_0.8fr_0.8fr_0.8fr_auto_auto]" onSubmit={handleSearch}>
          <input
            className="paper-input"
            value={filters.axiomType}
            onChange={(event) => updateFilter("axiomType", event.target.value)}
            placeholder="公理类型"
          />
          <Select value={filters.trueLabel} onChange={(value) => updateFilter("trueLabel", value)} options={[["", "真实标签"], ["1", "真实：正确"], ["0", "真实：错误"]]} />
          <Select value={filters.predictLabel} onChange={(value) => updateFilter("predictLabel", value)} options={[["", "预测标签"], ["1", "预测：正确"], ["0", "预测：错误"]]} />
          <Select value={filters.runStatus} onChange={(value) => updateFilter("runStatus", value)} options={[["", "执行状态"], ["success", "success"], ["failed", "failed"]]} />
          <Button type="submit" variant="secondary" disabled={isPending}>查询</Button>
          <Button type="button" variant="outline" onClick={resetFilters} disabled={isPending}>重置</Button>
        </form>

        {errorMessage ? <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div> : null}

        <div className="overflow-x-auto">
          <table className="paper-table min-w-[1120px]">
            <thead>
              <tr>
                <th>编号</th>
                <th>公理类型</th>
                <th>公理文本</th>
                <th>真实标签</th>
                <th>预测标签</th>
                <th>判断结果</th>
                <th>执行状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pageData.records.map((row) => (
                <tr key={row.id}>
                  <td>{row.id}</td>
                  <td>{row.axiomType || "--"}</td>
                  <td className="max-w-[420px] truncate" title={row.axiomText}>{row.axiomText || "--"}</td>
                  <td><LabelBadge value={row.trueLabel} /></td>
                  <td><LabelBadge value={row.predictLabel} /></td>
                  <td>{row.judgmentResult || "--"}</td>
                  <td><StatusBadge status={row.runStatus} /></td>
                  <td>
                    <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => setSelected(row)}>
                      查看详情
                    </Button>
                  </td>
                </tr>
              ))}
              {pageData.records.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center text-slate-500">暂无评估结果</td>
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
          <div className="paper-dialog max-w-4xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">评估结果详情</h3>
                <p className="mt-2 text-sm text-slate-600">查看解释信息、原始输出与错误信息。</p>
              </div>
              <Button variant="outline" onClick={() => setSelected(null)}>关闭</Button>
            </div>
            <div className="mt-6 grid gap-4">
              <DetailBlock label="公理文本" value={selected.axiomText} />
              <DetailBlock label="解释信息" value={selected.explanation || "--"} />
              <DetailBlock label="模型原始输出" value={selected.rawOutput || "--"} />
              <DetailBlock label="错误信息" value={selected.errorMessage || "--"} />
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}


function Select({ value, onChange, options }: { value: string; onChange: (value: string) => void; options: Array<[string, string]> }) {
  return (
    <select className="paper-input" value={value} onChange={(event) => onChange(event.target.value)}>
      {options.map(([optionValue, label]) => (
        <option key={label} value={optionValue}>{label}</option>
      ))}
    </select>
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


function StatusBadge({ status }: { status: string }) {
  return <Badge variant={status === "success" ? "success" : "warning"}>{status}</Badge>;
}


function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-2xl border border-line bg-mist/55 p-4 text-sm leading-7 text-slate-700">
        {value}
      </pre>
    </div>
  );
}
