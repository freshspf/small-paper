import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";


type TypeMetricItem = {
  axiomType: string;
  total: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};

type TypeMetricsProps = {
  items: TypeMetricItem[];
};


export function TypeMetrics({ items }: TypeMetricsProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-6 py-5">
        <div>
          <h3 className="text-lg font-semibold text-ink">按公理类型统计</h3>
          <p className="text-sm text-slate-600">展示各类公理的样本数与 Accuracy、Precision、Recall、F1。</p>
        </div>
        <Badge>真实接口</Badge>
      </div>
      <table className="paper-table">
        <thead>
          <tr>
            <th>公理类型</th>
            <th>样本数</th>
            <th>Accuracy</th>
            <th>Precision</th>
            <th>Recall</th>
            <th>F1</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.axiomType}>
              <td>{item.axiomType}</td>
              <td>{item.total}</td>
              <td>{item.accuracy.toFixed(3)}</td>
              <td>{item.precision.toFixed(3)}</td>
              <td>{item.recall.toFixed(3)}</td>
              <td>{item.f1.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
