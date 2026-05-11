import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { stabilityCase, stabilityLeaderboard } from "@/lib/mock-data";


export function StabilityPanel() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-ink">语义等价表达</h3>
              <p className="text-sm text-slate-600">用于稳定性评估展示的原型案例分析。</p>
            </div>
            <Badge>{stabilityCase.model}</Badge>
          </div>
          <div className="mt-5 rounded-2xl border border-line bg-white/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">原始公理</p>
            <p className="mt-3 text-lg font-medium text-ink">{stabilityCase.original}</p>
          </div>
          <div className="mt-5 space-y-3">
            {stabilityCase.variants.map((variant) => (
              <div key={variant.variant} className="rounded-xl border border-line bg-white/70 p-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-ink">{variant.variant}</p>
                  <Badge variant={variant.result === "正确" ? "success" : "warning"}>{variant.result}</Badge>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">{variant.expression}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-ink">一致性统计</h3>
          <div className="mt-5 space-y-5">
            <div className="rounded-2xl bg-white/70 p-5">
              <p className="text-sm text-slate-500">硬一致性</p>
              <p className="mt-2 text-3xl font-semibold text-ink">{stabilityCase.hardConsistency.toFixed(2)}</p>
            </div>
            <div className="rounded-2xl bg-white/70 p-5">
              <p className="text-sm text-slate-500">软一致性</p>
              <p className="mt-2 text-3xl font-semibold text-ink">{stabilityCase.softConsistency.toFixed(2)}</p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">模型稳定性对比</h3>
        <div className="mt-5 space-y-4">
          {stabilityLeaderboard.map((item) => (
            <div key={item.model} className="grid gap-4 rounded-xl border border-line bg-white/70 p-4 md:grid-cols-[1.2fr_1fr_1fr] md:items-center">
              <p className="font-medium text-ink">{item.model}</p>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-sageDark/80">硬一致性</p>
                <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-sage" style={{ width: `${item.hard * 100}%` }} />
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-sageDark/80">软一致性</p>
                <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-sand" style={{ width: `${item.soft * 100}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
