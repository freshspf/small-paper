import { PageTitle } from "@/components/ui/page-title";
import { EvaluationLauncher } from "@/components/evaluations/evaluation-launcher";
import { getEvaluationCreateOptions } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function NewEvaluationPage() {
  const options = await getEvaluationCreateOptions();

  return (
    <div className="space-y-8">
      <PageTitle
        title="新建评测"
        description="选择模型、数据集和提示词模板后，直接启动评测任务并查看任务状态。"
      />
      <EvaluationLauncher
        models={options.models}
        datasets={options.datasets}
        templates={options.templates}
      />
    </div>
  );
}
