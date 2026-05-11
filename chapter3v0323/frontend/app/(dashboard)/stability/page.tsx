import { PageTitle } from "@/components/ui/page-title";
import { StabilityPanel } from "@/components/stability/stability-panel";


export default function StabilityPage() {
  return (
    <div className="space-y-8">
      <PageTitle
        title="稳定性评估"
        description="针对同一公理的多种语义等价表达，分析模型判断的一致性与稳健性。"
      />
      <StabilityPanel />
    </div>
  );
}
