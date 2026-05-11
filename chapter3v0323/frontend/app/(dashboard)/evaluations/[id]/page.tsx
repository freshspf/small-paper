import Link from "next/link";

import { EvalReportPanel } from "@/components/evaluations/eval-report-panel";
import { EvalTaskResultsTable } from "@/components/evaluations/eval-task-results-table";
import { ExplanationEvalPanel } from "@/components/evaluations/explanation-eval-panel";
import { MetricsGrid } from "@/components/evaluations/metrics-grid";
import { StabilityEvalPanel } from "@/components/evaluations/stability-eval-panel";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { PageTitle } from "@/components/ui/page-title";
import {
  getEvalTaskDetail,
  getEvalTaskResults,
  getEvalReport,
  getExplanationEvalRecords,
  getExplanationEvalStats,
  getStabilityEvalRecords,
  getStabilityEvalTasks,
  getStabilityTemplates,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function EvaluationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const detail = await getEvalTaskDetail(id);
  const results = await getEvalTaskResults({
    taskId: Number(id),
    page: 1,
    pageSize: 20,
  });
  const [explanationStats, explanationRecords] = await Promise.all([
    getExplanationEvalStats(Number(id)),
    getExplanationEvalRecords({
      taskId: Number(id),
      page: 1,
      pageSize: 20,
    }),
  ]);
  const stabilityTemplates = await getStabilityTemplates();
  const stabilityTasks = await getStabilityEvalTasks(Number(id));
  const stabilityRecords = stabilityTasks[0]
    ? await getStabilityEvalRecords({
        stabilityTaskId: stabilityTasks[0].id,
        page: 1,
        pageSize: 20,
      })
    : { records: [], total: 0, page: 1, pageSize: 20 };
  const report = await getEvalReport(Number(id));

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <PageTitle
          title="评估任务详情"
          description="查看任务配置、分类指标、样本级模型输出与执行状态。"
        />
        <Link
          href="/evaluations"
          className="inline-flex items-center justify-center rounded-xl border border-line bg-white/88 px-4 py-2 text-sm font-medium text-ink shadow-sm transition-all hover:bg-mist"
        >
          返回评估任务管理
        </Link>
      </div>

      <Card className="p-6">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr_1fr_1fr_0.8fr]">
          <InfoItem label="任务名称" value={detail.task.taskName} />
          <InfoItem label="数据集" value={detail.dataset?.datasetName ?? detail.task.datasetName} />
          <InfoItem label="模型" value={detail.model?.modelName ?? detail.task.modelName} />
          <InfoItem label="提示词模板" value={detail.prompt?.templateName ?? detail.task.promptName} />
          <div>
            <p className="text-sm text-slate-500">任务状态</p>
            <div className="mt-2">
              <Badge variant={detail.task.taskStatus === "failed" ? "warning" : "success"}>
                {formatTaskStatus(detail.task.taskStatus)}
              </Badge>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 border-t border-line pt-5 md:grid-cols-4">
          <InfoItem label="总样本数" value={String(detail.task.totalCount)} />
          <InfoItem label="成功数" value={String(detail.task.successCount)} />
          <InfoItem label="失败数" value={String(detail.task.failCount)} />
          <InfoItem label="创建时间" value={detail.task.createdTime} />
        </div>
      </Card>

      <MetricsGrid
        accuracy={detail.metrics.accuracy}
        precision={detail.metrics.precision}
        recall={detail.metrics.recall}
        f1={detail.metrics.f1}
      />

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">指标说明</h3>
        <div className="mt-4 grid gap-4 text-sm leading-7 text-slate-600 md:grid-cols-2">
          <p>当前版本基于真实标签 trueLabel 与模型预测标签 predictLabel 计算 Accuracy、Precision、Recall、F1。</p>
          <p>有效计数为 {detail.metrics.evaluatedCount} 条；未解析出预测标签或执行失败的样本不进入指标分母，但会保留在结果列表中。</p>
        </div>
      </Card>

      <EvalReportPanel report={report} />

      <EvalTaskResultsTable taskId={Number(id)} initialPage={results} />

      <ExplanationEvalPanel
        taskId={Number(id)}
        initialStats={explanationStats}
        initialPage={explanationRecords}
      />

      <StabilityEvalPanel
        baseTaskId={Number(id)}
        templates={stabilityTemplates}
        initialTasks={stabilityTasks}
        initialRecordPage={stabilityRecords}
      />
    </div>
  );
}


function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-ink">{value || "--"}</p>
    </div>
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
