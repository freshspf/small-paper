import { PageTitle } from "@/components/ui/page-title";
import { JobsTable } from "@/components/evaluations/jobs-table";
import { getEvalDatasets, getEvalTasks, getModelConfigs, getPromptTemplateConfigsByFilter } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function EvaluationsPage() {
  const [jobs, datasets, models, prompts] = await Promise.all([
    getEvalTasks(),
    getEvalDatasets(),
    getModelConfigs(),
    getPromptTemplateConfigsByFilter({ taskType: "ontology_evaluation" }),
  ]);

  return (
    <div className="space-y-8">
      <PageTitle
        title="评估任务管理"
        description="配置数据集、模型与提示词模板，执行本体学习能力评估并查看分类指标。"
      />
      <JobsTable jobs={jobs} datasets={datasets} models={models} prompts={prompts} />
    </div>
  );
}
