import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { exportHistory, exportOptions } from "@/lib/mock-data";


export function ExportPanel() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-3">
        {exportOptions.map((item) => (
          <Card key={item.title} className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-ink">{item.title}</h3>
              <Badge>{item.count}</Badge>
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-600">{item.description}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              {item.formats.map((format) => (
                <Badge key={format} variant="muted">
                  {format}
                </Badge>
              ))}
            </div>
            <div className="mt-6 flex gap-3">
              <Button className="flex-1">生成导出</Button>
              <Button variant="outline" className="flex-1">
                预览
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-6 py-5">
          <div>
            <h3 className="text-lg font-semibold text-ink">最近导出记录</h3>
            <p className="text-sm text-slate-600">用于论文结果整理和附录准备的原型导出历史。</p>
          </div>
          <Badge variant="success">下载中心</Badge>
        </div>
        <table className="min-w-full text-sm">
          <thead className="bg-white/70 text-left text-slate-500">
            <tr>
              <th className="px-6 py-4 font-medium">导出编号</th>
              <th className="px-6 py-4 font-medium">资源类型</th>
              <th className="px-6 py-4 font-medium">格式</th>
              <th className="px-6 py-4 font-medium">创建时间</th>
              <th className="px-6 py-4 font-medium">状态</th>
              <th className="px-6 py-4 font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-card">
            {exportHistory.map((item) => (
              <tr key={item.id}>
                <td className="px-6 py-4 font-medium text-ink">{item.id}</td>
                <td className="px-6 py-4 text-slate-600">{item.resource}</td>
                <td className="px-6 py-4 text-slate-600">{item.format}</td>
                <td className="px-6 py-4 text-slate-600">{item.createdAt}</td>
                <td className="px-6 py-4">
                  <Badge variant={item.status === "已就绪" ? "success" : "warning"}>{item.status}</Badge>
                </td>
                <td className="px-6 py-4">
                  <Button variant="outline" className="px-3 py-2 text-xs">
                    下载
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
