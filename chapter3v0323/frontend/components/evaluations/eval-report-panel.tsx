"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { type EvalReportData } from "@/lib/api";


type EvalReportPanelProps = {
  report: EvalReportData;
};


export function EvalReportPanel({ report }: EvalReportPanelProps) {
  function exportReport() {
    const printWindow = window.open("", "_blank", "width=1200,height=900");
    if (!printWindow) {
      window.print();
      return;
    }

    printWindow.document.write(buildPrintableReport(report));
    printWindow.document.close();
  }

  return (
    <section id="eval-report-export" className="print-area space-y-6">
      <Card className="break-avoid overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-line px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">评估报告</h3>
            <p className="text-sm text-slate-600">汇总分类评估、解释能力评估与稳定性评估结果，支持浏览器打印导出 PDF。</p>
          </div>
          <div className="no-print flex flex-col gap-2 sm:flex-row sm:items-center">
            <p className="text-xs text-slate-500">导出方式：点击按钮后选择“保存为 PDF”。</p>
            <Button variant="secondary" onClick={exportReport}>导出评估报告</Button>
          </div>
        </div>

        <div className="grid gap-4 px-6 py-5 md:grid-cols-2 xl:grid-cols-3">
          <Info label="任务名称" value={report.taskInfo.taskName} />
          <Info label="数据集" value={report.taskInfo.datasetName} />
          <Info label="模型" value={report.taskInfo.modelName} />
          <Info label="提示词模板" value={report.taskInfo.promptName} />
          <Info label="创建时间" value={report.taskInfo.createdTime} />
          <Info label="任务状态" value={formatTaskStatus(report.taskInfo.taskStatus)} />
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-3">
        <ReportTable
          title="分类评估结果"
          rows={[
            ["总样本数", report.classification.totalCount],
            ["成功数", report.classification.successCount],
            ["失败数", report.classification.failCount],
            ["Accuracy", report.classification.accuracy.toFixed(4)],
            ["Precision", report.classification.precision.toFixed(4)],
            ["Recall", report.classification.recall.toFixed(4)],
            ["F1", report.classification.f1.toFixed(4)],
          ]}
        />
        <ReportTable
          title="解释能力评估结果"
          rows={[
            ["判断正确样本数", report.explanation.correctCaseCount],
            ["已标注样本数", report.explanation.annotatedCount],
            ["解释正确数", report.explanation.explanationCorrectCount],
            ["幻觉样本数", report.explanation.hallucinationCount],
            ["解释正确率", report.explanation.explanationAccuracy.toFixed(4)],
            ["幻觉率", report.explanation.hallucinationRate.toFixed(4)],
          ]}
        />
        <ReportTable
          title="稳定性评估结果"
          rows={[
            ["数据状态", report.stability.hasData ? "已有稳定性评估" : "暂无数据"],
            ["总扰动样本数", report.stability.totalCount],
            ["成功数", report.stability.successCount],
            ["失败数", report.stability.failCount],
            ["硬一致性", report.stability.hardConsistency.toFixed(4)],
            ["软一致性", report.stability.softConsistency.toFixed(4)],
          ]}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <BarChart title="分类指标图表" items={report.charts.classification} />
        <BarChart title="解释能力指标图表" items={report.charts.explanation} />
        <BarChart title="稳定性指标图表" items={report.charts.stability} />
      </div>
    </section>
  );
}


function buildPrintableReport(report: EvalReportData) {
  const classificationRows: Array<[string, string | number]> = [
    ["总样本数", report.classification.totalCount],
    ["成功数", report.classification.successCount],
    ["失败数", report.classification.failCount],
    ["Accuracy", report.classification.accuracy.toFixed(4)],
    ["Precision", report.classification.precision.toFixed(4)],
    ["Recall", report.classification.recall.toFixed(4)],
    ["F1", report.classification.f1.toFixed(4)],
  ];
  const explanationRows: Array<[string, string | number]> = [
    ["判断正确样本数", report.explanation.correctCaseCount],
    ["已标注样本数", report.explanation.annotatedCount],
    ["解释正确数", report.explanation.explanationCorrectCount],
    ["幻觉样本数", report.explanation.hallucinationCount],
    ["解释正确率", report.explanation.explanationAccuracy.toFixed(4)],
    ["幻觉率", report.explanation.hallucinationRate.toFixed(4)],
  ];
  const stabilityRows: Array<[string, string | number]> = [
    ["数据状态", report.stability.hasData ? "已有稳定性评估" : "暂无数据"],
    ["总扰动样本数", report.stability.totalCount],
    ["成功数", report.stability.successCount],
    ["失败数", report.stability.failCount],
    ["硬一致性", report.stability.hardConsistency.toFixed(4)],
    ["软一致性", report.stability.softConsistency.toFixed(4)],
  ];

  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(report.taskInfo.taskName)}-评估报告</title>
    <style>
      @page { size: A4; margin: 14mm; }
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; background: #ffffff; color: #1f2933; }
      body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; font-size: 13px; line-height: 1.6; }
      .report { max-width: 1040px; margin: 0 auto; }
      .header { border: 1px solid #d8dee4; border-radius: 14px; padding: 18px 20px; margin-bottom: 16px; background: #fbfcfb; }
      h1 { margin: 0; font-size: 22px; }
      h2 { margin: 0 0 10px; font-size: 16px; }
      .muted { color: #64748b; margin: 4px 0 0; }
      .info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 14px; }
      .info { border: 1px solid #d8dee4; border-radius: 12px; padding: 10px 12px; background: #ffffff; }
      .label { color: #64748b; font-size: 12px; }
      .value { margin-top: 4px; font-weight: 650; }
      .section-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
      .card { border: 1px solid #d8dee4; border-radius: 14px; background: #ffffff; overflow: hidden; break-inside: avoid; page-break-inside: avoid; }
      .card-title { padding: 12px 14px; border-bottom: 1px solid #d8dee4; background: #f5f7f7; font-weight: 700; }
      table { width: 100%; border-collapse: collapse; }
      td { padding: 9px 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
      tr:last-child td { border-bottom: 0; }
      td:first-child { color: #64748b; width: 52%; }
      td:last-child { font-weight: 650; color: #1f2933; }
      .chart-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
      .chart { padding: 14px; }
      .bar-row { margin-top: 10px; }
      .bar-meta { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; margin-bottom: 4px; }
      .bar-track { height: 11px; border-radius: 999px; background: #e5e7eb; overflow: hidden; }
      .bar-fill { height: 100%; border-radius: 999px; background: #8fa8a1; }
      @media print {
        .report { max-width: none; }
        .header, .card { break-inside: avoid; page-break-inside: avoid; }
      }
    </style>
  </head>
  <body>
    <main class="report">
      <section class="header">
        <h1>评估报告</h1>
        <p class="muted">分类评估、解释能力评估与稳定性评估综合汇总</p>
        <div class="info-grid">
          ${renderInfo("任务名称", report.taskInfo.taskName)}
          ${renderInfo("数据集", report.taskInfo.datasetName)}
          ${renderInfo("模型", report.taskInfo.modelName)}
          ${renderInfo("提示词模板", report.taskInfo.promptName)}
          ${renderInfo("创建时间", report.taskInfo.createdTime)}
          ${renderInfo("任务状态", formatTaskStatus(report.taskInfo.taskStatus))}
        </div>
      </section>
      <section class="section-grid">
        ${renderTable("分类评估结果", classificationRows)}
        ${renderTable("解释能力评估结果", explanationRows)}
        ${renderTable("稳定性评估结果", stabilityRows)}
      </section>
      <section class="chart-grid">
        ${renderChart("分类指标图表", report.charts.classification)}
        ${renderChart("解释能力指标图表", report.charts.explanation)}
        ${renderChart("稳定性指标图表", report.charts.stability)}
      </section>
    </main>
    <script>
      window.onload = () => {
        setTimeout(() => {
          window.focus();
          window.print();
        }, 120);
      };
    </script>
  </body>
</html>`;
}


function renderInfo(label: string, value: string) {
  return `<div class="info"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(value || "--")}</div></div>`;
}


function renderTable(title: string, rows: Array<[string, string | number]>) {
  return `<div class="card"><div class="card-title">${escapeHtml(title)}</div><table><tbody>${rows
    .map(([label, value]) => `<tr><td>${escapeHtml(label)}</td><td>${escapeHtml(String(value))}</td></tr>`)
    .join("")}</tbody></table></div>`;
}


function renderChart(title: string, items: Array<{ name: string; value: number }>) {
  return `<div class="card chart"><h2>${escapeHtml(title)}</h2>${items
    .map((item) => {
      const width = Math.max(Math.min(item.value, 1), 0) * 100;
      return `<div class="bar-row"><div class="bar-meta"><span>${escapeHtml(item.name)}</span><strong>${escapeHtml(item.value.toFixed(4))}</strong></div><div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div></div>`;
    })
    .join("")}</div>`;
}


function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}


function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white/75 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-base font-semibold text-ink">{value || "--"}</p>
    </div>
  );
}


function ReportTable({ title, rows }: { title: string; rows: Array<[string, string | number]> }) {
  return (
    <Card className="break-avoid overflow-hidden">
      <div className="border-b border-line px-5 py-4">
        <h4 className="font-semibold text-ink">{title}</h4>
      </div>
      <table className="paper-table">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <td className="w-1/2 text-slate-500">{label}</td>
              <td className="font-semibold text-ink">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}


function BarChart({ title, items }: { title: string; items: Array<{ name: string; value: number }> }) {
  return (
    <Card className="break-avoid p-5">
      <h4 className="font-semibold text-ink">{title}</h4>
      <div className="mt-5 space-y-4">
        {items.map((item) => {
          const width = Math.max(Math.min(item.value, 1), 0) * 100;
          return (
            <div key={item.name}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-600">{item.name}</span>
                <span className="text-ink">{item.value.toFixed(4)}</span>
              </div>
              <div className="h-4 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-sage" style={{ width: `${width}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}


function formatTaskStatus(status: string): string {
  const labelMap: Record<string, string> = {
    pending: "未评估",
    running: "评估中",
    stopping: "停止中",
    stopped: "已停止",
    success: "评估完成",
    completed: "部分完成",
    failed: "失败",
  };
  return labelMap[status] ?? status;
}
