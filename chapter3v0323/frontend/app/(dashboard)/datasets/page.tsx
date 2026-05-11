import { DatasetTable } from "@/components/datasets/dataset-table";
import { PageTitle } from "@/components/ui/page-title";
import { getEvalDatasets } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function DatasetsPage() {
  const datasets = await getEvalDatasets();

  return (
    <div className="space-y-8">
      <PageTitle
        title="评测数据管理"
        description="导入、管理和查看本体学习能力评估所需的 CSV 评测数据。"
      />
      <DatasetTable datasets={datasets} />
    </div>
  );
}
