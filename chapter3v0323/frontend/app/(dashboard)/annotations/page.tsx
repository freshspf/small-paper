import { PageTitle } from "@/components/ui/page-title";
import { AnnotationWorkspace } from "@/components/annotations/annotation-workspace";
import {
  getAnnotationResults,
  getEvaluationTasks,
  getExplanationStats,
  type AnnotationItemData,
  type ExplanationStatsData,
} from "@/lib/api";


export const dynamic = "force-dynamic";

export default async function AnnotationsPage() {
  const tasks = await getEvaluationTasks();
  const initialTaskId = tasks[0]?.id ?? "1";

  let initialItems: AnnotationItemData[] = [];
  let initialStats: ExplanationStatsData = {
    overall: {
      totalAnnotations: 0,
      correctCount: 0,
      hallucinationCount: 0,
      explanationAccuracy: 0,
      hallucinationRate: 0,
    },
    byModel: [],
  };

  try {
    [initialItems, initialStats] = await Promise.all([
      getAnnotationResults(initialTaskId),
      getExplanationStats(),
    ]);
  } catch {
    initialItems = [];
  }

  return (
    <div className="space-y-8">
      <PageTitle
        title="解释标注"
        description="展示评测结果列表，并支持对每条解释进行 correct、wrong、hallucination 人工标注。"
      />
      <AnnotationWorkspace
        tasks={tasks}
        initialTaskId={initialTaskId}
        initialItems={initialItems}
        initialStats={initialStats}
      />
    </div>
  );
}
