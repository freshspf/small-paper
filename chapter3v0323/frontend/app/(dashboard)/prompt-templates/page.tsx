import { TemplateManager } from "@/components/prompt-templates/template-manager";
import { PageTitle } from "@/components/ui/page-title";
import { getPromptTemplateConfigs } from "@/lib/api";

export const dynamic = "force-dynamic";


export default async function PromptTemplatesPage() {
  const templates = await getPromptTemplateConfigs();

  return (
    <div className="space-y-8">
      <PageTitle
        title="提示词配置"
        description="维护不同任务和层级的提示词模板，统一管理数量、领域、命名和实体定义开关。"
      />
      <TemplateManager templates={templates} />
    </div>
  );
}
