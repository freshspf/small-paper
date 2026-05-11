import { Card } from "@/components/ui/card";
import { promptTemplates } from "@/lib/mock-data";


export function Highlights() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">系统流程</h3>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {["模型配置", "数据集导入", "提示词选择", "评测与分析"].map((step, index) => (
            <div key={step} className="rounded-2xl border border-line bg-white/70 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
                步骤 {index + 1}
              </p>
              <p className="mt-3 text-base font-medium text-ink">{step}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">提示词策略</h3>
        <div className="mt-5 space-y-4">
          {promptTemplates.map((template) => (
            <div key={template.name} className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-sm font-semibold text-ink">{template.name}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.24em] text-sageDark">{template.type}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{template.summary}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
