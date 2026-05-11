"use client";

import { useState, useTransition } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  getEvalDatasetRecords,
  type EvalDatasetListItem,
  type EvalDatasetRecordItem,
  type EvalDatasetRecordPage,
} from "@/lib/api";


type DatasetRecordsViewerProps = {
  dataset: EvalDatasetListItem;
  initialPage: EvalDatasetRecordPage;
};

const PAGE_SIZE = 20;


export function DatasetRecordsViewer({ dataset, initialPage }: DatasetRecordsViewerProps) {
  const [records, setRecords] = useState(initialPage.records);
  const [total, setTotal] = useState(initialPage.total);
  const [page, setPage] = useState(initialPage.page);
  const [axiomType, setAxiomType] = useState("");
  const [label, setLabel] = useState("");
  const [source, setSource] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<EvalDatasetRecordItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const totalPages = Math.max(Math.ceil(total / PAGE_SIZE), 1);

  function loadRecords(nextPage: number) {
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getEvalDatasetRecords({
          datasetId: dataset.id,
          page: nextPage,
          pageSize: PAGE_SIZE,
          axiomType,
          label,
          source,
        });
        setRecords(result.records);
        setTotal(result.total);
        setPage(result.page);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取样本失败，请稍后重试。");
      }
    });
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadRecords(1);
  }

  function resetFilters() {
    setAxiomType("");
    setLabel("");
    setSource("");
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const result = await getEvalDatasetRecords({
          datasetId: dataset.id,
          page: 1,
          pageSize: PAGE_SIZE,
        });
        setRecords(result.records);
        setTotal(result.total);
        setPage(result.page);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取样本失败，请稍后重试。");
      }
    });
  }

  return (
    <>
      <Card className="overflow-hidden">
        <div className="border-b border-line px-6 py-5">
          <h3 className="text-lg font-semibold text-ink">样本列表</h3>
          <p className="text-sm text-slate-600">支持按公理类型、标签和来源筛选，列表页仅显示上下文摘要。</p>
        </div>

        <form className="grid gap-3 border-b border-line bg-white/40 px-6 py-4 lg:grid-cols-[1fr_0.7fr_1fr_auto_auto]" onSubmit={handleSearch}>
          <input
            className="paper-input"
            value={axiomType}
            onChange={(event) => setAxiomType(event.target.value)}
            placeholder="公理类型，例如 subClassOf"
          />
          <select className="paper-input" value={label} onChange={(event) => setLabel(event.target.value)}>
            <option value="">全部标签</option>
            <option value="1">正确 1</option>
            <option value="0">错误 0</option>
          </select>
          <input
            className="paper-input"
            value={source}
            onChange={(event) => setSource(event.target.value)}
            placeholder="数据来源"
          />
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

        <div className="overflow-x-auto">
          <table className="paper-table min-w-[1180px]">
            <thead>
              <tr>
                <th>编号</th>
                <th>公理类型</th>
                <th>主语</th>
                <th>谓语</th>
                <th>宾语</th>
                <th>标签</th>
                <th>来源</th>
                <th>公理文本</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id}>
                  <td>{record.id}</td>
                  <td>{record.axiomType}</td>
                  <td className="max-w-[170px] truncate">{record.subject}</td>
                  <td>{record.predicate}</td>
                  <td className="max-w-[170px] truncate">{record.object}</td>
                  <td>
                    <Badge variant={record.label === 1 ? "success" : "warning"}>
                      {record.label === 1 ? "正确" : "错误"}
                    </Badge>
                  </td>
                  <td>{record.source}</td>
                  <td className="max-w-[260px] truncate">{record.axiomText}</td>
                  <td>
                    <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => setSelectedRecord(record)}>
                      查看详情
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-line px-6 py-4 text-sm text-slate-600">
          <span>
            共 {total} 条，第 {page} / {totalPages} 页
          </span>
          <div className="flex gap-2">
            <Button variant="outline" disabled={page <= 1 || isPending} onClick={() => loadRecords(page - 1)}>
              上一页
            </Button>
            <Button variant="outline" disabled={page >= totalPages || isPending} onClick={() => loadRecords(page + 1)}>
              下一页
            </Button>
          </div>
        </div>
      </Card>

      {selectedRecord ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-5xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">样本详情</h3>
                <p className="mt-2 text-sm text-slate-600">{selectedRecord.axiomText}</p>
              </div>
              <Button variant="outline" onClick={() => setSelectedRecord(null)}>
                关闭
              </Button>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <InfoBlock title="负例构造策略" value={selectedRecord.negativeStrategy || "无"} />
              <InfoBlock title="上下文摘要" value={selectedRecord.contextSummary || "无"} />
              <InfoBlock title="主语上下文" value={selectedRecord.subjectContext || "无"} />
              <InfoBlock title="宾语上下文" value={selectedRecord.objectContext || "无"} />
              <div className="md:col-span-2">
                <InfoBlock title="综合上下文信息" value={selectedRecord.contextInfo || selectedRecord.contextSummary || "无"} />
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}


function InfoBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white/75 p-4">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 max-h-52 overflow-y-auto whitespace-pre-wrap text-sm leading-7 text-ink">{value}</p>
    </div>
  );
}
