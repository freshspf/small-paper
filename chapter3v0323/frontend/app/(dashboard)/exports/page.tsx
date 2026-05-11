import { PageTitle } from "@/components/ui/page-title";
import { ExportPanel } from "@/components/exports/export-panel";


export default function ExportsPage() {
  return (
    <div className="space-y-8">
      <PageTitle
        title="导出中心"
        description="统一管理评测结果、解释标注和本体结构文件的导出。"
      />
      <ExportPanel />
    </div>
  );
}
