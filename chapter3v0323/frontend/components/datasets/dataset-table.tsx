"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  deleteEvalDataset,
  type EvalDatasetListItem,
  uploadEvalDataset,
} from "@/lib/api";


type DatasetTableProps = {
  datasets: EvalDatasetListItem[];
};


export function DatasetTable({ datasets }: DatasetTableProps) {
  const [items, setItems] = useState(datasets);
  const [keyword, setKeyword] = useState("");
  const [isPending, startTransition] = useTransition();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [datasetName, setDatasetName] = useState("");
  const [remark, setRemark] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const filteredItems = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    if (!normalizedKeyword) {
      return items;
    }
    return items.filter((item) => item.datasetName.toLowerCase().includes(normalizedKeyword));
  }, [items, keyword]);

  const totalRecords = useMemo(
    () => items.reduce((total, item) => total + item.recordCount, 0),
    [items],
  );

  function resetForm() {
    setDatasetName("");
    setRemark("");
    setFile(null);
    setErrorMessage(null);
  }

  function closeDialog() {
    setIsDialogOpen(false);
    resetForm();
  }

  function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setErrorMessage("请选择一个 CSV 文件。");
      return;
    }

    setMessage(null);
    setErrorMessage(null);
    const formData = new FormData();
    formData.append("datasetName", datasetName);
    formData.append("remark", remark);
    formData.append("file", file);

    startTransition(async () => {
      try {
        const result = await uploadEvalDataset(formData);
        setItems((current) => [result.dataset, ...current]);
        setMessage(`上传成功：共 ${result.totalCount} 条，成功导入 ${result.successCount} 条。`);
        closeDialog();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "上传失败，请稍后重试。");
      }
    });
  }

  function handleDelete(dataset: EvalDatasetListItem) {
    const confirmed = window.confirm(`确认删除数据集“${dataset.datasetName}”及其全部样本吗？`);
    if (!confirmed) {
      return;
    }

    setMessage(null);
    setErrorMessage(null);
    startTransition(async () => {
      try {
        await deleteEvalDataset(dataset.id);
        setItems((current) => current.filter((item) => item.id !== dataset.id));
        setMessage(`已删除数据集：${dataset.datasetName}`);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "删除失败，请稍后重试。");
      }
    });
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">数据集总数</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{items.length}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">样本总数</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{totalRecords}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">存储方式</p>
          <p className="mt-2 text-lg font-semibold text-ink">解析入库</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-line px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">评测数据集列表</h3>
            <p className="text-sm text-slate-600">上传 CSV 后直接解析入库，仅保留文件名和数据集元信息。</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              className="paper-input min-w-[260px]"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="按数据集名称搜索"
            />
            <Button variant="secondary" onClick={() => setIsDialogOpen(true)}>
              上传 CSV
            </Button>
          </div>
        </div>

        {message ? (
          <div className="border-b border-line bg-emerald-50 px-6 py-3 text-sm text-emerald-700">{message}</div>
        ) : null}
        {errorMessage ? (
          <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div>
        ) : null}

        {filteredItems.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-base font-medium text-ink">当前没有评测数据集</p>
            <p className="mt-2 text-sm text-slate-500">可以点击“上传 CSV”导入评测样本。</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="paper-table min-w-[980px]">
              <thead>
                <tr>
                  <th>编号</th>
                  <th>数据集名称</th>
                  <th>原始文件名</th>
                  <th>样本数量</th>
                  <th>备注</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>{dataset.id}</td>
                    <td className="font-medium text-ink">{dataset.datasetName}</td>
                    <td>{dataset.fileName}</td>
                    <td>{dataset.recordCount}</td>
                    <td className="max-w-[240px] truncate">{dataset.remark || "--"}</td>
                    <td>{dataset.createdTime}</td>
                    <td>
                      <div className="flex gap-2">
                        <Link
                          href={`/datasets/${dataset.id}`}
                          className="inline-flex items-center justify-center rounded-xl border border-line bg-white/88 px-3 py-2 text-xs font-medium text-ink shadow-sm transition-all hover:bg-mist"
                        >
                          查看样本
                        </Link>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => handleDelete(dataset)}>
                          删除
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">上传评测数据集</h3>
                <p className="mt-2 text-sm text-slate-600">系统会校验字段并逐行解析入库，不长期保存原始 CSV 文件。</p>
              </div>
              <Button variant="outline" onClick={closeDialog}>
                关闭
              </Button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleUpload}>
              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">数据集名称</span>
                <input
                  className="paper-input"
                  value={datasetName}
                  onChange={(event) => setDatasetName(event.target.value)}
                  placeholder="例如：DBpedia RDFS 评测集"
                  required
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">备注</span>
                <textarea
                  className="paper-textarea"
                  value={remark}
                  onChange={(event) => setRemark(event.target.value)}
                  placeholder="说明该数据集的来源、用途或实验批次。"
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium text-ink">CSV 文件</span>
                <input
                  type="file"
                  accept=".csv"
                  className="paper-input file:mr-4 file:rounded-lg file:border-0 file:bg-mist file:px-3 file:py-2"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  required
                />
              </label>

              <div className="rounded-2xl border border-line bg-white/70 p-4 text-sm leading-7 text-slate-600">
                必填字段：axiom_type、subject、predicate、object、label、source、axiom_text。label 只能为 0 或 1。
              </div>

              {errorMessage ? <p className="text-sm text-amber-700">{errorMessage}</p> : null}

              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={closeDialog}>
                  取消
                </Button>
                <Button type="submit" variant="secondary" disabled={isPending}>
                  {isPending ? "上传中..." : "开始上传"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
