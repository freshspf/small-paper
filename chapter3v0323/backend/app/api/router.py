from fastapi import APIRouter

from app.api.routes import (
    datasets,
    eval_datasets,
    eval_reports,
    eval_tasks,
    evaluations,
    explanation_evals,
    health,
    llm_models,
    model_configs,
    ontology_results,
    ontology_tasks,
    prompt_template_configs,
    prompt_templates,
    stability_evals,
)


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(llm_models.router, prefix="/models", tags=["models"])
api_router.include_router(model_configs.router, prefix="/model-configs", tags=["model-configs"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(eval_datasets.router, prefix="/eval-datasets", tags=["eval-datasets"])
api_router.include_router(eval_reports.router, prefix="/eval-reports", tags=["eval-reports"])
api_router.include_router(eval_tasks.router, prefix="/eval-tasks", tags=["eval-tasks"])
api_router.include_router(explanation_evals.router, prefix="/explanation-evals", tags=["explanation-evals"])
api_router.include_router(stability_evals.router, prefix="/stability-evals", tags=["stability-evals"])
api_router.include_router(ontology_tasks.router, prefix="/ontology-tasks", tags=["ontology-tasks"])
api_router.include_router(ontology_results.router, prefix="/ontology-results", tags=["ontology-results"])
api_router.include_router(
    prompt_template_configs.router,
    prefix="/prompt-templates/configs",
    tags=["prompt-template-configs"],
)
api_router.include_router(prompt_templates.router, prefix="/prompt-templates", tags=["prompt-templates"])
api_router.include_router(
    prompt_template_configs.router,
    prefix="/prompt-template-configs",
    tags=["prompt-template-configs"],
)
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
