import Link from "next/link";

import { DatasetRecordsViewer } from "@/components/datasets/dataset-records-viewer";
import { Card } from "@/components/ui/card";
import { PageTitle } from "@/components/ui/page-title";
import { getEvalDatasetDetail, getEvalDatasetRecords } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function DatasetDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const dataset = await getEvalDatasetDetail(id);
  const initialPage = await getEvalDatasetRecords({
    datasetId: dataset.id,
    page: 1,
    pageSize: 20,
  });

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <PageTitle
          title={dataset.datasetName}
          description="查看评测数据集元信息、筛选样本记录，并检查每条样本的上下文信息。"
        />
        <Link
          href="/datasets"
          className="inline-flex items-center justify-center rounded-xl border border-line bg-white/88 px-4 py-2.5 text-sm font-medium text-ink shadow-sm transition-all hover:bg-mist"
        >
          返回列表
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-5">
          <p className="text-sm text-slate-500">原始文件名</p>
          <p className="mt-3 truncate text-lg font-semibold text-ink">{dataset.fileName}</p>
        </Card>
        <Card className="p-5">
          <p className="text-sm text-slate-500">样本数量</p>
          <p className="mt-3 text-2xl font-semibold text-ink">{dataset.recordCount}</p>
        </Card>
        <Card className="p-5">
          <p className="text-sm text-slate-500">创建时间</p>
          <p className="mt-3 text-lg font-semibold text-ink">{dataset.createdTime}</p>
        </Card>
        <Card className="p-5">
          <p className="text-sm text-slate-500">存储方式</p>
          <p className="mt-3 text-lg font-semibold text-ink">解析入库</p>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">数据集备注</h3>
        <p className="mt-3 text-sm leading-7 text-slate-700">{dataset.remark || "暂无备注"}</p>
      </Card>

      <DatasetRecordsViewer dataset={dataset} initialPage={initialPage} />
    </div>
  );
}
