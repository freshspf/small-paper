import { PageTitle } from "@/components/ui/page-title";
import { OntologyTaskManager } from "@/components/ontology/ontology-task-manager";
import { getModelConfigs, getOntologyTasks, getPromptTemplateConfigsByFilter } from "@/lib/api";


export default async function OntologyPage() {
  const [tasks, models, prompts] = await Promise.all([
    getOntologyTasks().catch(() => []),
    getModelConfigs(),
    getPromptTemplateConfigsByFilter({}),
  ]);

  return (
    <div className="space-y-8">
      <PageTitle
        title="本体学习任务管理"
        description="面向第四章本体学习实验，支持配置优化实验任务创建、动态提示词组装、模型调用与结果查看。"
      />
      <OntologyTaskManager initialTasks={tasks} models={models} prompts={prompts} />
    </div>
  );
}
