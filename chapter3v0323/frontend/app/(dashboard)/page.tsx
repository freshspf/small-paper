import Link from "next/link";

import { StatCard } from "@/components/dashboard/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageTitle } from "@/components/ui/page-title";
import { getDashboardStats } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function DashboardPage() {
  const stats = await getDashboardStats();
  const dashboardMetrics = [
    {
      title: "模型数量",
      value: String(stats.modelCount),
      description: "系统已接入并可用于评测的大语言模型数量",
    },
    {
      title: "数据集数量",
      value: String(stats.datasetCount),
      description: "已导入的 RDFS 公理数据集与实验样本集合",
    },
    {
      title: "评测任务数量",
      value: String(stats.evaluationCount),
      description: "系统中已创建的评测任务与实验运行记录",
    },
    {
      title: "已标注数量",
      value: String(stats.annotationCount),
      description: "解释能力人工标注总数，可用于幻觉率与正确率分析",
    },
  ];

  const entryCards = [
    {
      title: "模型配置",
      description: "管理大语言模型的名称、接口地址、密钥与默认模型设置。",
      href: "/models",
      tag: "LLM",
    },
    {
      title: "数据集管理",
      description: "上传和预览 RDFS 公理数据集，支持 CSV 导入与样本查看。",
      href: "/datasets",
      tag: "Dataset",
    },
    {
      title: "提示词模板",
      description: "统一管理基础型、指令增强型和上下文引导型提示词模板。",
      href: "/prompt-templates",
      tag: "Prompt",
    },
    {
      title: "评测任务",
      description: "发起评测任务，串联模型、数据集与提示词模板形成完整流程。",
      href: "/evaluations",
      tag: "Task",
    },
    {
      title: "结果分析",
      description: "查看 Accuracy、Precision、Recall、F1 与按公理类型统计结果。",
      href: "/evaluations/1",
      tag: "Metrics",
    },
    {
      title: "解释标注",
      description: "对模型解释进行 correct、wrong、hallucination 人工标注。",
      href: "/annotations",
      tag: "Annotation",
    },
  ];

  return (
    <div className="space-y-8">
      <PageTitle
        title="基于大语言模型的RDFS本体学习与评估系统"
        description="系统围绕模型配置、数据集导入、提示词管理、批量评测、结果分析与解释标注构建完整业务链路。"
        action={
          <Link href="/evaluations/new">
            <Button>新建评测</Button>
          </Link>
        }
      />

      <Card className="overflow-hidden border-sage/20 bg-[radial-gradient(circle_at_top_left,rgba(143,168,161,0.22),transparent_35%),radial-gradient(circle_at_bottom_right,rgba(216,195,165,0.22),transparent_28%),linear-gradient(180deg,#fcfdfd_0%,#f6f8f9_100%)]">
        <div className="grid gap-8 px-6 py-7 xl:grid-cols-[1.1fr_0.9fr] xl:px-8 xl:py-8">
          <div>
            <Badge className="bg-sageDark text-white">系统概览</Badge>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight text-ink">
              RDFS 本体学习与评估一体化管理系统
            </h2>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">
              本系统聚焦大语言模型在 RDFS 本体公理判断、解释生成与稳定性分析中的表现，形成从数据集导入、提示词配置到评测分析与人工标注的完整演示链路。
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Badge variant="muted">RDFS Ontology</Badge>
              <Badge variant="muted">LLM Evaluation</Badge>
              <Badge variant="muted">Explanation Annotation</Badge>
              <Badge variant="muted">Stability Analysis</Badge>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {dashboardMetrics.map((metric) => (
              <StatCard key={metric.title} {...metric} />
            ))}
          </div>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-6 py-5">
          <div>
            <h2 className="text-lg font-semibold text-ink">功能入口</h2>
            <p className="text-sm text-slate-600">按系统业务流程组织核心模块入口，支持快速进入各项管理功能。</p>
          </div>
          <Badge>系统总览</Badge>
        </div>

        <div className="grid gap-5 p-6 md:grid-cols-2 xl:grid-cols-3">
          {entryCards.map((item) => (
            <Link key={item.title} href={item.href}>
              <div className="group h-full rounded-2xl border border-line bg-white/75 p-5 transition-all hover:-translate-y-0.5 hover:border-sage hover:shadow-soft">
                <div className="flex items-center justify-between">
                  <Badge>{item.tag}</Badge>
                  <span className="text-sm text-slate-400 transition-colors group-hover:text-sageDark">
                    进入模块
                  </span>
                </div>
                <h3 className="mt-5 text-xl font-semibold text-ink">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-600">{item.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-ink">系统说明</h2>
              <p className="text-sm text-slate-600">聚焦 RDFS 本体公理评测与解释能力分析的管理系统。</p>
            </div>
            <Badge variant="success">运行中</Badge>
          </div>
          <div className="mt-5 space-y-4 text-sm leading-7 text-slate-600">
            <p>
              系统支持多个大语言模型接入，能够围绕 RDFS 本体公理完成数据导入、提示词配置、批量评测、结果统计与解释标注。
            </p>
            <p>
              当前版本覆盖模型配置、数据集管理、评测任务、结果统计和人工标注等核心功能模块。
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-ink">展示流程</h2>
              <p className="text-sm text-slate-600">建议按以下顺序演示系统核心能力。</p>
            </div>
            <Badge variant="muted">Demo Flow</Badge>
          </div>
          <div className="mt-5 space-y-4">
            {[
              "1. 配置大语言模型",
              "2. 上传并预览数据集",
              "3. 选择提示词模板",
              "4. 发起评测任务",
              "5. 查看指标与结果分析",
              "6. 完成解释人工标注",
            ].map((step) => (
              <div key={step} className="rounded-xl border border-line bg-white/70 px-4 py-3 text-sm text-slate-700">
                {step}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
