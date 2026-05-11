import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { recentEvaluations } from "@/lib/mock-data";


export function RecentEvaluations() {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">最近评测任务</h3>
          <p className="text-sm text-slate-600">展示系统近期创建与执行的评测任务。</p>
        </div>
        <Badge>实时预览</Badge>
      </div>
      <div className="mt-6 overflow-hidden rounded-xl border border-line">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-white/70 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Job ID</th>
              <th className="px-4 py-3 font-medium">模型</th>
              <th className="px-4 py-3 font-medium">数据集</th>
              <th className="px-4 py-3 font-medium">模板</th>
              <th className="px-4 py-3 font-medium">状态</th>
              <th className="px-4 py-3 font-medium">准确率</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-card">
            {recentEvaluations.map((job) => (
              <tr key={job.id}>
                <td className="px-4 py-3 font-medium text-ink">{job.id}</td>
                <td className="px-4 py-3 text-slate-600">{job.model}</td>
                <td className="px-4 py-3 text-slate-600">{job.dataset}</td>
                <td className="px-4 py-3 text-slate-600">{job.template}</td>
                <td className="px-4 py-3">
                  <Badge variant={job.status === "已完成" ? "success" : "warning"}>{job.status}</Badge>
                </td>
                <td className="px-4 py-3 font-medium text-ink">{job.accuracy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
