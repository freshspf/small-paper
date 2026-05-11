import { Card } from "@/components/ui/card";


type MetricsGridProps = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};


export function MetricsGrid({ accuracy, precision, recall, f1 }: MetricsGridProps) {
  const items = [
    { label: "准确率", value: accuracy },
    { label: "精确率", value: precision },
    { label: "召回率", value: recall },
    { label: "F1 值", value: f1 },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label} className="p-5">
          <p className="text-sm text-slate-500">{item.label}</p>
          <p className="mt-3 text-3xl font-semibold text-ink">{item.value.toFixed(3)}</p>
        </Card>
      ))}
    </div>
  );
}
