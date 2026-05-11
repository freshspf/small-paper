import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { type EvaluationResultRow } from "@/lib/mock-data";


type ResultTableProps = {
  rows: EvaluationResultRow[];
};


export function ResultTable({ rows }: ResultTableProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-line px-6 py-5">
        <h3 className="text-lg font-semibold text-ink">样本级结果</h3>
        <p className="text-sm text-slate-600">展示评测输出中的代表性样本，便于查看模型判断与解释内容。</p>
      </div>
      <table className="paper-table">
        <thead>
          <tr>
            <th>样本编号</th>
            <th>公理类型</th>
            <th>公理文本</th>
            <th>判断结果</th>
            <th>解释</th>
            <th>响应时间</th>
            <th>Token 数</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.sampleId}>
              <td>{row.sampleId}</td>
              <td>{row.axiomType}</td>
              <td>{row.axiomText}</td>
              <td>
                <Badge variant={row.judgment === "正确" ? "success" : "warning"}>{row.judgment}</Badge>
              </td>
              <td>{row.explanation}</td>
              <td>{row.responseTime}</td>
              <td>{row.tokens}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
