import { ModelTable } from "@/components/models/model-table";
import { PageTitle } from "@/components/ui/page-title";
import { getModelConfigs } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function ModelsPage() {
  const models = await getModelConfigs();

  return (
    <div className="space-y-8">
      <PageTitle
        title="模型管理"
        description="维护大语言模型调用配置，包括调用标识、接口地址、密钥、温度参数、最大输出长度和启用状态。"
      />
      <ModelTable models={models} />
    </div>
  );
}
