import { Card } from "@/components/ui/card";


type PlaceholderPanelProps = {
  title: string;
  description: string;
};


export function PlaceholderPanel({ title, description }: PlaceholderPanelProps) {
  return (
      <Card className="p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-sageDark/80">
        下一阶段
        </p>
      <h3 className="mt-3 text-2xl font-semibold text-ink">{title}</h3>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">{description}</p>
        <div className="mt-6 rounded-2xl border border-dashed border-line bg-white/70 p-5 text-sm text-slate-500">
        该模块将在下一阶段继续完善，目前页面已满足原型导航和论文截图展示需求。
        </div>
      </Card>
  );
}
