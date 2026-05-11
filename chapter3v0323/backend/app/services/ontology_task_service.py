from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.model_config import ModelConfig
from app.models.ontology_chunk import OntologyChunk
from app.models.ontology_chunk_result import OntologyChunkResult
from app.models.ontology_task import OntologyTask
from app.models.prompt_template_config import PromptTemplateConfig
from app.schemas.ontology_task import OntologyBaselineCreate, OntologyLayeredCreate, OntologyTaskCreate
from app.services.model_call_service import call_openai_compatible_model

try:
    import PyPDF2  # type: ignore
except ImportError:  # pragma: no cover
    import pypdf as PyPDF2  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHAPTER4_PROMPT_DIR = PROJECT_ROOT / "chapter4" / "prompts"
TEMPLATE_PATH = CHAPTER4_PROMPT_DIR / "template" / "configurable_template.txt"
MODULE_PATHS = {
    "count": CHAPTER4_PROMPT_DIR / "modules" / "count_on.txt",
    "naming": CHAPTER4_PROMPT_DIR / "modules" / "naming_on.txt",
    "entity": CHAPTER4_PROMPT_DIR / "modules" / "entity_on.txt",
}
DOMAIN_PATHS = {
    "geography": CHAPTER4_PROMPT_DIR / "modules" / "domain_geography.txt",
    "medical": CHAPTER4_PROMPT_DIR / "modules" / "domain_medical.txt",
    "transportation": CHAPTER4_PROMPT_DIR / "modules" / "domain_transportation.txt",
}
UPLOAD_DIR = PROJECT_ROOT / "backend" / "storage" / "ontology_tasks"

BASELINE_PROMPT_TEMPLATE = """You are an ontology construction system. Your task is to construct a conservative RDFS ontology directly from a single raw text chunk.

{domain_context}

CORE INSTRUCTIONS:

1. Work only on the current chunk.
   - Do not assume information from other chunks.
   - Do not merge with unseen context.

2. Extract ontology elements conservatively:
   - Classes: abstract concepts explicitly supported by the chunk.
   - Properties: relations explicitly supported by the chunk.

3. Keep the ontology minimal and high-confidence:
   - Use only terms and relations clearly grounded in the chunk.
   - Do not invent additional terms.
   - Do not perform ontology completion.
   - If evidence is weak, omit the axiom.

4. Construct hierarchy very strictly:
   - Infer rdfs:subClassOf only when the chunk explicitly states or very directly implies a subclass relation.
   - Infer rdfs:subPropertyOf only when the chunk clearly supports it.

5. Infer domain and range very strictly:
   - Only assign domain/range when the subject/object typing is explicit in the current chunk.
   - Do not guess missing domain/range.

6. Use consistent naming:
   - Classes in PascalCase.
   - Properties in camelCase.
   - Avoid vague names and unnecessary variants.

7. Output only what the current chunk supports.
   - Conservative extraction is preferred over completeness.

OUTPUT FORMAT:
Return a valid JSON object with the following structure:
{{
  "classes": [...],
  "properties": [...],
  "subClassOf": [
    {{"sub": "...", "super": "..."}}
  ],
  "subPropertyOf": [
    {{"sub": "...", "super": "..."}}
  ],
  "domain": [
    {{"property": "...", "class": "..."}}
  ],
  "range": [
    {{"property": "...", "class": "..."}}
  ]
}}

INPUT CHUNK METADATA:
- chunk_id: {chunk_id}
- section_title: {section_title}
- page_start: {page_start}
- page_end: {page_end}

INPUT TEXT CHUNK:
{text}
"""


def _read_text(path: Path, fallback: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return fallback


def _replace_placeholder(prompt: str, name: str, value: str) -> str:
    prompt = prompt.replace(f"{{{name}}}", value)
    prompt = prompt.replace(f"{{{{{name}}}}}", value)
    return prompt


def build_configuration_prompt(payload: OntologyTaskCreate, template: PromptTemplateConfig) -> str:
    base_template = _read_text(TEMPLATE_PATH, template.templateContent)
    if not base_template:
        base_template = template.templateContent

    domain_key = payload.domainType.strip().lower()
    if domain_key not in DOMAIN_PATHS:
        raise ValueError("领域类型必须是 geography、medical 或 transportation")

    replacements = {
        "COUNT_CONSTRAINT": _read_text(MODULE_PATHS["count"]) if payload.switchCount == 1 else "",
        "DOMAIN_HINT": _read_text(DOMAIN_PATHS[domain_key]) if payload.switchDomain == 1 else "",
        "NAMING_RULES": _read_text(MODULE_PATHS["naming"]) if payload.switchNaming == 1 else "",
        "ENTITY_DEFINITION": _read_text(MODULE_PATHS["entity"]) if payload.switchEntityDefinition == 1 else "",
    }

    final_prompt = base_template
    for name, value in replacements.items():
        final_prompt = _replace_placeholder(final_prompt, name, value)

    input_text = payload.inputText.strip()
    if "{text}" in final_prompt:
        final_prompt = final_prompt.replace("{text}", input_text)
    elif "{{text}}" in final_prompt:
        final_prompt = final_prompt.replace("{{text}}", input_text)
    else:
        final_prompt = f"{final_prompt.rstrip()}\n\n**INPUT TEXT:**\n{input_text}"

    return final_prompt


def create_and_run_ontology_task(db: Session, payload: OntologyTaskCreate) -> OntologyTask:
    if payload.taskType != "configuration_optimization":
        raise ValueError("当前版本仅支持配置优化实验")

    model = db.get(ModelConfig, payload.modelId)
    if model is None or model.status != 1:
        raise ValueError("请选择已启用的模型配置")

    template = db.get(PromptTemplateConfig, payload.promptId)
    if template is None or template.status != 1:
        raise ValueError("请选择已启用的提示词模板")
    if template.taskType != "configuration_optimization" or template.templateType != "configurable":
        raise ValueError("配置优化实验只能选择配置优化统一模板")

    final_prompt = build_configuration_prompt(payload, template)
    task = OntologyTask(
        taskName=payload.taskName.strip(),
        taskType=payload.taskType,
        modelId=payload.modelId,
        promptId=payload.promptId,
        domainType=payload.domainType.strip().lower(),
        executionMode="configuration_optimization",
        inputType="text",
        switchCount=payload.switchCount,
        switchDomain=payload.switchDomain,
        switchNaming=payload.switchNaming,
        switchEntityDefinition=payload.switchEntityDefinition,
        inputText=payload.inputText.strip(),
        finalPrompt=final_prompt,
        taskStatus="running",
        remark=payload.remark,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        output, _, _ = call_openai_compatible_model(model, final_prompt)
        task.outputContent = output
        task.taskStatus = "completed"
        task.errorMessage = None
    except Exception as exc:
        task.outputContent = None
        task.taskStatus = "failed"
        task.errorMessage = str(exc)[:255]

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_ontology_tasks(
    db: Session,
    task_name: Optional[str] = None,
    task_type: Optional[str] = None,
) -> List[dict[str, Any]]:
    stmt = select(OntologyTask).order_by(OntologyTask.updatedTime.desc(), OntologyTask.id.desc())
    if task_name:
        stmt = stmt.where(OntologyTask.taskName.like(f"%{task_name.strip()}%"))
    if task_type:
        stmt = stmt.where(OntologyTask.taskType == task_type.strip())
    return [build_task_read(db, task) for task in db.scalars(stmt)]


def get_ontology_task(db: Session, task_id: int) -> Optional[dict[str, Any]]:
    task = db.get(OntologyTask, task_id)
    if task is None:
        return None
    return build_task_read(db, task)


def delete_ontology_task(db: Session, task_id: int) -> bool:
    task = db.get(OntologyTask, task_id)
    if task is None:
        return False
    db.execute(delete(OntologyChunkResult).where(OntologyChunkResult.taskId == task_id))
    db.execute(delete(OntologyChunk).where(OntologyChunk.taskId == task_id))
    db.delete(task)
    db.commit()
    return True


def create_baseline_task(db: Session, payload: OntologyBaselineCreate, filename: str, content: bytes) -> OntologyTask:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("请上传 PDF 文件")

    model = db.get(ModelConfig, payload.modelId)
    if model is None or model.status != 1:
        raise ValueError("请选择已启用的模型配置")

    template = db.get(PromptTemplateConfig, payload.promptId)
    if template is None or template.status != 1:
        raise ValueError("请选择已启用的 baseline 提示词模板")
    if template.taskType != "ontology_learning" or template.templateType != "baseline":
        raise ValueError("本体学习 baseline 只能选择 baseline 提示词")

    domain_key = payload.domainType.strip().lower()
    if domain_key not in DOMAIN_PATHS:
        raise ValueError("领域类型必须是 geography、medical 或 transportation")

    task_uuid = uuid.uuid4().hex[:12]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", filename)
    task_dir = UPLOAD_DIR / task_uuid
    task_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = task_dir / safe_name
    pdf_path.write_bytes(content)

    task = OntologyTask(
        taskName=payload.taskName.strip(),
        taskType="ontology_learning",
        executionMode="baseline",
        modelId=payload.modelId,
        promptId=payload.promptId,
        domainType=domain_key,
        domainSwitch=payload.domainSwitch,
        chunkMetadataSwitch=payload.chunkMetadataSwitch,
        inputType="pdf",
        fileName=filename,
        filePath=str(pdf_path),
        inputText=None,
        finalPrompt=None,
        outputContent=None,
        mergedOutput=None,
        taskStatus="pending",
        remark=payload.remark,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def create_layered_task(db: Session, payload: OntologyLayeredCreate, filename: str, content: bytes) -> OntologyTask:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("请上传 PDF 文件")

    model = db.get(ModelConfig, payload.modelId)
    if model is None or model.status != 1:
        raise ValueError("请选择已启用的模型配置")

    semantic_template = validate_layer_template(db, payload.semanticPromptId, "meaning")
    term_template = validate_layer_template(db, payload.termPromptId, "term")
    concept_template = validate_layer_template(db, payload.conceptPromptId, "concept")

    domain_key = payload.domainType.strip().lower()
    if domain_key not in DOMAIN_PATHS:
        raise ValueError("领域类型必须是 geography、medical 或 transportation")

    task_uuid = uuid.uuid4().hex[:12]
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", filename)
    task_dir = UPLOAD_DIR / task_uuid
    task_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = task_dir / safe_name
    pdf_path.write_bytes(content)

    task = OntologyTask(
        taskName=payload.taskName.strip(),
        taskType="ontology_learning",
        executionMode="layered",
        modelId=payload.modelId,
        promptId=concept_template.id,
        semanticPromptId=semantic_template.id,
        termPromptId=term_template.id,
        conceptPromptId=concept_template.id,
        domainType=domain_key,
        domainSwitch=payload.domainSwitch,
        chunkMetadataSwitch=payload.chunkMetadataSwitch,
        inputType="pdf",
        fileName=filename,
        filePath=str(pdf_path),
        inputText=None,
        finalPrompt=None,
        outputContent=None,
        mergedOutput=None,
        taskStatus="pending",
        remark=payload.remark,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def validate_layer_template(db: Session, template_id: int, template_type: str) -> PromptTemplateConfig:
    template = db.get(PromptTemplateConfig, template_id)
    if template is None or template.status != 1:
        raise ValueError("请选择已启用的三层提示词模板")
    if template.taskType != "ontology_learning" or template.templateType != template_type:
        raise ValueError(f"请选择 {template_type} 类型的本体学习提示词模板")
    return template


def run_baseline_task_background(task_id: int) -> None:
    with SessionLocal() as db:
        task = db.get(OntologyTask, task_id)
        if task is None:
            return
        try:
            task.taskStatus = "running"
            db.add(task)
            db.commit()
            chunks = split_pdf_to_chunks(Path(str(task.filePath)))
            task.totalChunkCount = len(chunks)
            db.add(task)
            db.commit()

            db.execute(delete(OntologyChunkResult).where(OntologyChunkResult.taskId == task.id))
            db.execute(delete(OntologyChunk).where(OntologyChunk.taskId == task.id))
            db.commit()

            chunk_records = []
            for index, chunk in enumerate(chunks, start=1):
                record = OntologyChunk(
                    taskId=task.id,
                    chunkId=str(chunk["id"]),
                    chunkIndex=index,
                    sectionTitle=str(chunk.get("metadata", {}).get("section_title", "")),
                    pageStart=chunk.get("metadata", {}).get("page_start"),
                    pageEnd=chunk.get("metadata", {}).get("page_end"),
                    chunkText=str(chunk.get("text", "")),
                )
                db.add(record)
                db.flush()
                chunk_records.append(record)
            db.commit()

            model = db.get(ModelConfig, task.modelId)
            if model is None:
                raise ValueError("模型配置不存在")

            for chunk in chunk_records:
                db.refresh(task)
                if task.taskStatus == "stopping":
                    task.taskStatus = "stopped"
                    db.add(task)
                    db.commit()
                    break
                prompt = build_baseline_prompt(task, chunk)
                output = ""
                parsed: dict[str, Any] | None = None
                try:
                    output, _, _ = call_openai_compatible_model(model, prompt)
                    parsed = parse_baseline_output(output)
                    result = OntologyChunkResult(
                        taskId=task.id,
                        chunkRecordId=chunk.id,
                        executionMode="baseline",
                        layerName="baseline",
                        finalPrompt=prompt,
                        outputContent=output,
                        parsedOutput=json.dumps(parsed, ensure_ascii=False),
                        runStatus="success",
                    )
                    task.successCount += 1
                except Exception as exc:
                    result = OntologyChunkResult(
                        taskId=task.id,
                        chunkRecordId=chunk.id,
                        executionMode="baseline",
                        layerName="baseline",
                        finalPrompt=prompt,
                        outputContent=output,
                        parsedOutput=json.dumps(empty_baseline_output(), ensure_ascii=False),
                        runStatus="failed",
                        errorMessage=str(exc)[:255],
                    )
                    task.failCount += 1

                db.add(result)
                db.add(task)
                db.commit()

            db.refresh(task)
            if task.taskStatus not in {"stopped", "stopping"}:
                task.mergedOutput = json.dumps(merge_task_outputs(db, task.id), ensure_ascii=False, indent=2)
                task.outputContent = task.mergedOutput
                task.taskStatus = "completed" if task.failCount == 0 else "partial_success"
                db.add(task)
                db.commit()
        except Exception as exc:
            task = db.get(OntologyTask, task_id)
            if task is not None:
                task.taskStatus = "failed"
                task.errorMessage = str(exc)[:255]
                db.add(task)
                db.commit()


def run_layered_task_background(task_id: int) -> None:
    with SessionLocal() as db:
        task = db.get(OntologyTask, task_id)
        if task is None:
            return
        try:
            task.taskStatus = "running"
            db.add(task)
            db.commit()
            chunks = split_pdf_to_chunks(Path(str(task.filePath)))
            task.totalChunkCount = len(chunks)
            db.add(task)
            db.commit()

            db.execute(delete(OntologyChunkResult).where(OntologyChunkResult.taskId == task.id))
            db.execute(delete(OntologyChunk).where(OntologyChunk.taskId == task.id))
            db.commit()

            chunk_records = []
            for index, chunk in enumerate(chunks, start=1):
                record = OntologyChunk(
                    taskId=task.id,
                    chunkId=str(chunk["id"]),
                    chunkIndex=index,
                    sectionTitle=str(chunk.get("metadata", {}).get("section_title", "")),
                    pageStart=chunk.get("metadata", {}).get("page_start"),
                    pageEnd=chunk.get("metadata", {}).get("page_end"),
                    chunkText=str(chunk.get("text", "")),
                )
                db.add(record)
                db.flush()
                chunk_records.append(record)
            db.commit()

            model = db.get(ModelConfig, task.modelId)
            semantic_template = db.get(PromptTemplateConfig, task.semanticPromptId)
            term_template = db.get(PromptTemplateConfig, task.termPromptId)
            concept_template = db.get(PromptTemplateConfig, task.conceptPromptId)
            if model is None or semantic_template is None or term_template is None or concept_template is None:
                raise ValueError("模型或三层提示词模板不存在")

            for chunk in chunk_records:
                db.refresh(task)
                if task.taskStatus == "stopping":
                    task.taskStatus = "stopped"
                    db.add(task)
                    db.commit()
                    break

                try:
                    meaning_prompt = build_layer_prompt(task, semantic_template, chunk, input_payload=chunk.chunkText, layer_name="semantic_network")
                    meaning_raw, _, _ = call_openai_compatible_model(model, meaning_prompt)
                    meaning_parsed = parse_json_output(meaning_raw)
                    save_layer_result(db, task.id, chunk.id, "semantic_network", meaning_prompt, meaning_raw, meaning_parsed, "success")

                    term_prompt = build_layer_prompt(task, term_template, chunk, input_payload=json.dumps(meaning_parsed, ensure_ascii=False), layer_name="term_refinement")
                    term_raw, _, _ = call_openai_compatible_model(model, term_prompt)
                    term_parsed = parse_json_output(term_raw)
                    save_layer_result(db, task.id, chunk.id, "term_refinement", term_prompt, term_raw, term_parsed, "success")

                    concept_prompt = build_layer_prompt(task, concept_template, chunk, input_payload=json.dumps(term_parsed, ensure_ascii=False), layer_name="concept_modeling")
                    concept_raw, _, _ = call_openai_compatible_model(model, concept_prompt)
                    concept_parsed = parse_baseline_output(concept_raw)
                    save_layer_result(db, task.id, chunk.id, "concept_modeling", concept_prompt, concept_raw, concept_parsed, "success")
                    task.successCount += 1
                except Exception as exc:
                    save_layer_result(
                        db,
                        task.id,
                        chunk.id,
                        "concept_modeling",
                        "",
                        "",
                        empty_baseline_output(),
                        "failed",
                        str(exc)[:255],
                    )
                    task.failCount += 1

                db.add(task)
                db.commit()

            db.refresh(task)
            if task.taskStatus not in {"stopped", "stopping"}:
                task.mergedOutput = json.dumps(merge_task_outputs(db, task.id), ensure_ascii=False, indent=2)
                task.outputContent = task.mergedOutput
                task.taskStatus = "completed" if task.failCount == 0 else "partial_success"
                db.add(task)
                db.commit()
        except Exception as exc:
            task = db.get(OntologyTask, task_id)
            if task is not None:
                task.taskStatus = "failed"
                task.errorMessage = str(exc)[:255]
                db.add(task)
                db.commit()


def stop_ontology_task(db: Session, task_id: int) -> Optional[OntologyTask]:
    task = db.get(OntologyTask, task_id)
    if task is None:
        return None
    if task.taskStatus in {"running", "pending"}:
        task.taskStatus = "stopping"
        db.add(task)
        db.commit()
        db.refresh(task)
    return task


def split_pdf_to_chunks(pdf_path: Path, max_chunk_size: int = 5000) -> list[dict[str, Any]]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    reader = PyPDF2.PdfReader(str(pdf_path))
    chunks: list[dict[str, Any]] = []
    chunk_index = 1
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        parts = split_text_by_size(text, max_chunk_size)
        for part_index, part in enumerate(parts, start=1):
            chunks.append(
                {
                    "id": f"page_{page_index}_chunk_{part_index}",
                    "text": part,
                    "metadata": {
                        "section_title": f"Page {page_index}",
                        "page_start": page_index,
                        "page_end": page_index,
                        "chunk_index": chunk_index,
                    },
                }
            )
            chunk_index += 1
    if not chunks:
        raise ValueError("PDF 未解析到有效文本")
    return chunks


def split_text_by_size(text: str, max_chunk_size: int) -> list[str]:
    if len(text) <= max_chunk_size:
        return [text]
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chunk_size:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            chunks.append(current)
        current = sentence
    if current:
        chunks.append(current)
    return chunks


def build_baseline_prompt(task: OntologyTask, chunk: OntologyChunk) -> str:
    domain_context = _read_text(DOMAIN_PATHS[task.domainType]) if task.domainSwitch == 1 else ""
    section_title = chunk.sectionTitle or ""
    page_start = "" if chunk.pageStart is None else str(chunk.pageStart)
    page_end = "" if chunk.pageEnd is None else str(chunk.pageEnd)
    if task.chunkMetadataSwitch != 1:
        section_title = ""
        page_start = ""
        page_end = ""
    return BASELINE_PROMPT_TEMPLATE.format(
        domain_context=domain_context,
        chunk_id=chunk.chunkId,
        section_title=section_title,
        page_start=page_start,
        page_end=page_end,
        text=chunk.chunkText,
    )


def build_layer_prompt(
    task: OntologyTask,
    template: PromptTemplateConfig,
    chunk: OntologyChunk,
    input_payload: str,
    layer_name: str,
) -> str:
    domain_context = _read_text(DOMAIN_PATHS[task.domainType]) if task.domainSwitch == 1 else ""
    section_title = chunk.sectionTitle or ""
    page_start = "" if chunk.pageStart is None else str(chunk.pageStart)
    page_end = "" if chunk.pageEnd is None else str(chunk.pageEnd)
    if task.chunkMetadataSwitch != 1:
        section_title = ""
        page_start = ""
        page_end = ""

    prompt = template.templateContent
    replacements = {
        "domain_context": domain_context,
        "DOMAIN_CONTEXT": domain_context,
        "chunk_id": chunk.chunkId,
        "section_title": section_title,
        "page_start": page_start,
        "page_end": page_end,
        "text": input_payload,
        "input": input_payload,
        "layer_input": input_payload,
        "previous_output": input_payload,
        "meaning_output": input_payload,
        "term_output": input_payload,
    }
    for key, value in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

    if input_payload not in prompt:
        prompt = (
            f"{prompt.rstrip()}\n\n"
            f"LAYER NAME:\n{layer_name}\n\n"
            f"CHUNK METADATA:\n"
            f"- chunk_id: {chunk.chunkId}\n"
            f"- section_title: {section_title}\n"
            f"- page_start: {page_start}\n"
            f"- page_end: {page_end}\n\n"
            f"LAYER INPUT:\n{input_payload}"
        )
    return prompt


def save_layer_result(
    db: Session,
    task_id: int,
    chunk_id: int,
    layer_name: str,
    prompt: str,
    raw: str,
    parsed: dict[str, Any],
    status: str,
    error: Optional[str] = None,
) -> None:
    result = OntologyChunkResult(
        taskId=task_id,
        chunkRecordId=chunk_id,
        executionMode="layered",
        layerName=layer_name,
        finalPrompt=prompt,
        outputContent=raw,
        parsedOutput=json.dumps(parsed, ensure_ascii=False),
        runStatus=status,
        errorMessage=error,
    )
    db.add(result)
    db.commit()


def parse_json_output(raw: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("模型输出 JSON 必须是对象")
    return data


def parse_baseline_output(raw: str) -> dict[str, Any]:
    cleaned = strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("模型输出 JSON 必须是对象")
    return normalize_baseline_output(data)


def strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def empty_baseline_output() -> dict[str, Any]:
    return {
        "classes": [],
        "properties": [],
        "subClassOf": [],
        "subPropertyOf": [],
        "domain": [],
        "range": [],
    }


def normalize_baseline_output(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "classes": normalize_string_list(data.get("classes", [])),
        "properties": normalize_string_list(data.get("properties", [])),
        "subClassOf": normalize_pair_list(data.get("subClassOf", []), "sub", "super"),
        "subPropertyOf": normalize_pair_list(data.get("subPropertyOf", []), "sub", "super"),
        "domain": normalize_pair_list(data.get("domain", []), "property", "class"),
        "range": normalize_pair_list(data.get("range", []), "property", "class"),
    }


def normalize_string_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    values: list[str] = []
    seen = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def normalize_pair_list(items: Any, left_key: str, right_key: str) -> list[dict[str, str]]:
    if not isinstance(items, list):
        return []
    values: list[dict[str, str]] = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        left = str(item.get(left_key, "")).strip()
        right = str(item.get(right_key, "")).strip()
        if not left or not right:
            continue
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        values.append({left_key: left, right_key: right})
    return values


def merge_task_outputs(db: Session, task_id: int) -> dict[str, Any]:
    merged = empty_baseline_output()
    task = db.get(OntologyTask, task_id)
    layer_filter = "concept_modeling" if task and task.executionMode == "layered" else "baseline"
    results = db.scalars(
        select(OntologyChunkResult).where(
            OntologyChunkResult.taskId == task_id,
            OntologyChunkResult.runStatus == "success",
            OntologyChunkResult.layerName == layer_filter,
        )
    )
    for result in results:
        parsed = json.loads(result.parsedOutput or "{}")
        merged["classes"] = merge_string_list(merged["classes"], parsed.get("classes", []))
        merged["properties"] = merge_string_list(merged["properties"], parsed.get("properties", []))
        merged["subClassOf"] = merge_pair_list(merged["subClassOf"] + parsed.get("subClassOf", []), "sub", "super")
        merged["subPropertyOf"] = merge_pair_list(merged["subPropertyOf"] + parsed.get("subPropertyOf", []), "sub", "super")
        merged["domain"] = merge_pair_list(merged["domain"] + parsed.get("domain", []), "property", "class")
        merged["range"] = merge_pair_list(merged["range"] + parsed.get("range", []), "property", "class")
    return merged


def merge_string_list(left: list[str], right: list[str]) -> list[str]:
    values = []
    seen = set()
    for item in left + right:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def merge_pair_list(items: list[dict[str, str]], left_key: str, right_key: str) -> list[dict[str, str]]:
    return normalize_pair_list(items, left_key, right_key)


def get_task_stats(db: Session, task_id: int) -> dict[str, int]:
    task = db.get(OntologyTask, task_id)
    merged = json.loads(task.mergedOutput or "{}") if task and task.mergedOutput else empty_baseline_output()
    layer_success = {"semanticNetworkSuccessCount": 0, "termRefinementSuccessCount": 0, "conceptModelingSuccessCount": 0}
    for result in db.scalars(select(OntologyChunkResult).where(OntologyChunkResult.taskId == task_id, OntologyChunkResult.runStatus == "success")):
        if result.layerName == "semantic_network":
            layer_success["semanticNetworkSuccessCount"] += 1
        elif result.layerName == "term_refinement":
            layer_success["termRefinementSuccessCount"] += 1
        elif result.layerName == "concept_modeling":
            layer_success["conceptModelingSuccessCount"] += 1
    return {
        "totalChunkCount": task.totalChunkCount if task else 0,
        "successCount": task.successCount if task else 0,
        "failCount": task.failCount if task else 0,
        "classCount": len(merged.get("classes", [])),
        "propertyCount": len(merged.get("properties", [])),
        "subClassOfCount": len(merged.get("subClassOf", [])),
        "subPropertyOfCount": len(merged.get("subPropertyOf", [])),
        "domainCount": len(merged.get("domain", [])),
        "rangeCount": len(merged.get("range", [])),
        **layer_success,
    }


def list_task_chunks(db: Session, task_id: int) -> list[dict[str, Any]]:
    chunks = list(db.scalars(select(OntologyChunk).where(OntologyChunk.taskId == task_id).order_by(OntologyChunk.chunkIndex.asc())))
    task = db.get(OntologyTask, task_id)
    preferred_layer = "concept_modeling" if task and task.executionMode == "layered" else "baseline"
    result_map = {}
    for result in db.scalars(select(OntologyChunkResult).where(OntologyChunkResult.taskId == task_id)):
        if result.layerName == preferred_layer or result.chunkRecordId not in result_map:
            result_map[result.chunkRecordId] = result
    return [build_chunk_read(chunk, result_map.get(chunk.id)) for chunk in chunks]


def get_chunk_detail(db: Session, task_id: int, chunk_id: int) -> Optional[dict[str, Any]]:
    chunk = db.get(OntologyChunk, chunk_id)
    if chunk is None or chunk.taskId != task_id:
        return None
    results = list(db.scalars(select(OntologyChunkResult).where(OntologyChunkResult.chunkRecordId == chunk.id).order_by(OntologyChunkResult.id.asc())))
    result = next((item for item in results if item.layerName in {"concept_modeling", "baseline"}), results[-1] if results else None)
    return {
        "chunk": build_chunk_read(chunk, result, include_text=True),
        "result": build_result_read(result) if result else None,
        "layerResults": [build_result_read(item) for item in results],
    }


def build_chunk_read(chunk: OntologyChunk, result: Optional[OntologyChunkResult], include_text: bool = False) -> dict[str, Any]:
    parsed = json.loads(result.parsedOutput or "{}") if result and result.parsedOutput else empty_baseline_output()
    text = chunk.chunkText if include_text else (chunk.chunkText[:180] + "..." if len(chunk.chunkText) > 180 else chunk.chunkText)
    return {
        "id": chunk.id,
        "taskId": chunk.taskId,
        "chunkId": chunk.chunkId,
        "chunkIndex": chunk.chunkIndex,
        "sectionTitle": chunk.sectionTitle,
        "pageStart": chunk.pageStart,
        "pageEnd": chunk.pageEnd,
        "chunkText": text,
        "createdTime": chunk.createdTime,
        "updatedTime": chunk.updatedTime,
        "resultId": result.id if result else None,
        "runStatus": result.runStatus if result else "pending",
        "semanticNetworkStatus": get_layer_status(chunk.taskId, chunk.id, "semantic_network"),
        "termRefinementStatus": get_layer_status(chunk.taskId, chunk.id, "term_refinement"),
        "conceptModelingStatus": get_layer_status(chunk.taskId, chunk.id, "concept_modeling"),
        "errorMessage": result.errorMessage if result else None,
        "classCount": len(parsed.get("classes", [])),
        "propertyCount": len(parsed.get("properties", [])),
        "subClassOfCount": len(parsed.get("subClassOf", [])),
        "subPropertyOfCount": len(parsed.get("subPropertyOf", [])),
        "domainCount": len(parsed.get("domain", [])),
        "rangeCount": len(parsed.get("range", [])),
    }


def build_result_read(result: OntologyChunkResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "taskId": result.taskId,
        "chunkRecordId": result.chunkRecordId,
        "executionMode": result.executionMode,
        "layerName": result.layerName,
        "finalPrompt": result.finalPrompt,
        "outputContent": result.outputContent,
        "parsedOutput": json.loads(result.parsedOutput or "{}"),
        "runStatus": result.runStatus,
        "errorMessage": result.errorMessage,
        "createdTime": result.createdTime,
        "updatedTime": result.updatedTime,
    }


def get_layer_status(task_id: int, chunk_id: int, layer_name: str) -> Optional[str]:
    with SessionLocal() as db:
        result = db.scalar(
            select(OntologyChunkResult).where(
                OntologyChunkResult.taskId == task_id,
                OntologyChunkResult.chunkRecordId == chunk_id,
                OntologyChunkResult.layerName == layer_name,
            )
        )
        return result.runStatus if result else None


def build_task_read(db: Session, task: OntologyTask) -> dict[str, Any]:
    model = db.get(ModelConfig, task.modelId)
    template = db.get(PromptTemplateConfig, task.promptId)
    return {
        "id": task.id,
        "taskName": task.taskName,
        "taskType": task.taskType,
        "executionMode": task.executionMode,
        "modelId": task.modelId,
        "promptId": task.promptId,
        "semanticPromptId": task.semanticPromptId,
        "termPromptId": task.termPromptId,
        "conceptPromptId": task.conceptPromptId,
        "domainType": task.domainType,
        "domainSwitch": task.domainSwitch,
        "chunkMetadataSwitch": task.chunkMetadataSwitch,
        "inputType": task.inputType,
        "fileName": task.fileName,
        "filePath": task.filePath,
        "totalChunkCount": task.totalChunkCount,
        "successCount": task.successCount,
        "failCount": task.failCount,
        "switchCount": task.switchCount,
        "switchDomain": task.switchDomain,
        "switchNaming": task.switchNaming,
        "switchEntityDefinition": task.switchEntityDefinition,
        "inputText": task.inputText,
        "finalPrompt": task.finalPrompt,
        "outputContent": task.outputContent,
        "mergedOutput": task.mergedOutput,
        "taskStatus": task.taskStatus,
        "errorMessage": task.errorMessage,
        "remark": task.remark,
        "createdTime": task.createdTime,
        "updatedTime": task.updatedTime,
        "modelName": model.modelName if model else None,
        "promptName": template.templateName if template else None,
    }
