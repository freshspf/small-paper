from __future__ import annotations

import json
import re
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.ontology_axiom_result import OntologyAxiomResult
from app.models.ontology_chunk_result import OntologyChunkResult
from app.models.ontology_task import OntologyTask


AXIOM_TYPES = ["class", "property", "subClassOf", "subPropertyOf", "domain", "range"]


def ensure_axiom_results(db: Session, task_id: int) -> None:
    existing = db.scalar(select(OntologyAxiomResult.id).where(OntologyAxiomResult.taskId == task_id).limit(1))
    if existing is not None:
        return
    sync_axiom_results(db, task_id)


def sync_axiom_results(db: Session, task_id: int) -> None:
    task = db.get(OntologyTask, task_id)
    if task is None:
        raise ValueError("本体学习任务不存在")

    merged = _load_merged_output(task)
    execution_mode = task.executionMode or "unknown"
    source_layer = "concept_modeling" if execution_mode == "layered" else "baseline"

    db.execute(delete(OntologyAxiomResult).where(OntologyAxiomResult.taskId == task_id))
    for record in normalize_axioms(merged, execution_mode, source_layer):
        db.add(OntologyAxiomResult(taskId=task_id, **record))
    db.commit()


def get_task_result(db: Session, task_id: int, axiom_type: Optional[str] = None) -> dict[str, Any]:
    task = db.get(OntologyTask, task_id)
    if task is None:
        raise ValueError("本体学习任务不存在")
    ensure_axiom_results(db, task_id)

    stmt = select(OntologyAxiomResult).where(OntologyAxiomResult.taskId == task_id).order_by(
        OntologyAxiomResult.axiomType.asc(),
        OntologyAxiomResult.id.asc(),
    )
    if axiom_type and axiom_type != "all":
        stmt = stmt.where(OntologyAxiomResult.axiomType == axiom_type)
    axioms = list(db.scalars(stmt))
    all_axioms = list(db.scalars(select(OntologyAxiomResult).where(OntologyAxiomResult.taskId == task_id)))
    stats = build_stats(task, all_axioms)
    return {
        "task": {
            "id": task.id,
            "taskName": task.taskName,
            "executionMode": task.executionMode,
            "domainType": task.domainType,
            "taskStatus": task.taskStatus,
            "fileName": task.fileName,
            "totalChunkCount": task.totalChunkCount,
            "successCount": task.successCount,
            "failCount": task.failCount,
            "createdTime": task.createdTime,
            "updatedTime": task.updatedTime,
        },
        "overview": stats,
        "axioms": [build_axiom_read(item) for item in axioms],
        "graph": build_graph_data(all_axioms),
        "charts": build_chart_data(task, stats),
    }


def get_export_content(db: Session, task_id: int, fmt: str) -> dict[str, str]:
    task = db.get(OntologyTask, task_id)
    if task is None:
        raise ValueError("本体学习任务不存在")
    ensure_axiom_results(db, task_id)
    axioms = list(db.scalars(select(OntologyAxiomResult).where(OntologyAxiomResult.taskId == task_id).order_by(OntologyAxiomResult.id.asc())))
    fmt = fmt.lower()
    if fmt == "json":
        content = json.dumps([build_axiom_read(item) for item in axioms], ensure_ascii=False, indent=2)
        filename = f"ontology_task_{task_id}_{task.executionMode}.json"
    elif fmt == "ttl":
        content = build_turtle(axioms)
        filename = f"ontology_task_{task_id}_{task.executionMode}.ttl"
    elif fmt == "rdfxml":
        content = build_rdfxml(axioms)
        filename = f"ontology_task_{task_id}_{task.executionMode}.rdf"
    elif fmt == "owlapi":
        content = build_owlapi(axioms)
        filename = f"ontology_task_{task_id}_{task.executionMode}.txt"
    else:
        raise ValueError("导出格式必须是 json、ttl、rdfxml 或 owlapi")
    return {"format": fmt, "filename": filename, "content": content}


def get_layer_results(db: Session, task_id: int) -> dict[str, Any]:
    task = db.get(OntologyTask, task_id)
    if task is None:
        raise ValueError("本体学习任务不存在")
    rows = list(
        db.scalars(
            select(OntologyChunkResult)
            .where(OntologyChunkResult.taskId == task_id)
            .order_by(OntologyChunkResult.chunkRecordId.asc(), OntologyChunkResult.id.asc())
        )
    )
    grouped: dict[str, list[dict[str, Any]]] = {
        "semantic_network": [],
        "term_refinement": [],
        "concept_modeling": [],
    }
    for row in rows:
        if row.layerName in grouped:
            grouped[row.layerName].append(
                {
                    "id": row.id,
                    "chunkRecordId": row.chunkRecordId,
                    "layerName": row.layerName,
                    "runStatus": row.runStatus,
                    "errorMessage": row.errorMessage,
                    "finalPrompt": row.finalPrompt,
                    "outputContent": row.outputContent,
                    "parsedOutput": _loads(row.parsedOutput),
                    "createdTime": row.createdTime,
                    "updatedTime": row.updatedTime,
                }
            )
    return {"taskId": task_id, "executionMode": task.executionMode, "layers": grouped}


def normalize_axioms(merged: dict[str, Any], execution_mode: str, source_layer: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in merged.get("classes", []) or []:
        subject = str(name).strip()
        if subject:
            rows.append(make_row(execution_mode, source_layer, "class", subject, "", f"Class({subject})", subject))
    for name in merged.get("properties", []) or []:
        subject = str(name).strip()
        if subject:
            rows.append(make_row(execution_mode, source_layer, "property", subject, "", f"Property({subject})", subject))
    for item in merged.get("subClassOf", []) or []:
        if isinstance(item, dict):
            subject, obj = str(item.get("sub", "")).strip(), str(item.get("super", "")).strip()
            if subject and obj:
                rows.append(make_row(execution_mode, source_layer, "subClassOf", subject, obj, f"{subject} rdfs:subClassOf {obj}", item))
    for item in merged.get("subPropertyOf", []) or []:
        if isinstance(item, dict):
            subject, obj = str(item.get("sub", "")).strip(), str(item.get("super", "")).strip()
            if subject and obj:
                rows.append(make_row(execution_mode, source_layer, "subPropertyOf", subject, obj, f"{subject} rdfs:subPropertyOf {obj}", item))
    for item in merged.get("domain", []) or []:
        if isinstance(item, dict):
            subject, obj = str(item.get("property", "")).strip(), str(item.get("class", "")).strip()
            if subject and obj:
                rows.append(make_row(execution_mode, source_layer, "domain", subject, obj, f"{subject} rdfs:domain {obj}", item))
    for item in merged.get("range", []) or []:
        if isinstance(item, dict):
            subject, obj = str(item.get("property", "")).strip(), str(item.get("class", "")).strip()
            if subject and obj:
                rows.append(make_row(execution_mode, source_layer, "range", subject, obj, f"{subject} rdfs:range {obj}", item))
    return rows


def make_row(execution_mode: str, source_layer: str, axiom_type: str, subject: str, obj: str, text: str, payload: Any) -> dict[str, Any]:
    return {
        "executionMode": execution_mode,
        "sourceLayer": source_layer,
        "axiomType": axiom_type,
        "subjectTerm": subject,
        "objectTerm": obj or None,
        "axiomText": text,
        "payloadJson": json.dumps(payload, ensure_ascii=False),
    }


def build_stats(task: OntologyTask, axioms: list[OntologyAxiomResult]) -> dict[str, Any]:
    counts = {key: 0 for key in AXIOM_TYPES}
    for item in axioms:
        if item.axiomType in counts:
            counts[item.axiomType] += 1
    return {
        **counts,
        "executionMode": task.executionMode,
        "totalChunkCount": task.totalChunkCount,
        "successCount": task.successCount,
        "failCount": task.failCount,
    }


def build_axiom_read(item: OntologyAxiomResult) -> dict[str, Any]:
    return {
        "id": item.id,
        "taskId": item.taskId,
        "executionMode": item.executionMode,
        "sourceLayer": item.sourceLayer,
        "axiomType": item.axiomType,
        "subjectTerm": item.subjectTerm,
        "objectTerm": item.objectTerm,
        "axiomText": item.axiomText,
        "payloadJson": _loads(item.payloadJson),
        "createdTime": item.createdTime,
        "updatedTime": item.updatedTime,
    }


def build_graph_data(axioms: list[OntologyAxiomResult]) -> dict[str, Any]:
    nodes: dict[str, dict[str, str]] = {}
    edges = []
    for item in axioms:
        if item.axiomType == "class" and item.subjectTerm:
            nodes.setdefault(item.subjectTerm, {"id": item.subjectTerm, "label": item.subjectTerm, "type": "class"})
        elif item.axiomType == "property" and item.subjectTerm:
            nodes.setdefault(item.subjectTerm, {"id": item.subjectTerm, "label": item.subjectTerm, "type": "property"})
        elif item.subjectTerm and item.objectTerm:
            source_type = "property" if item.axiomType in {"subPropertyOf", "domain", "range"} else "class"
            target_type = "property" if item.axiomType == "subPropertyOf" else "class"
            nodes.setdefault(item.subjectTerm, {"id": item.subjectTerm, "label": item.subjectTerm, "type": source_type})
            nodes.setdefault(item.objectTerm, {"id": item.objectTerm, "label": item.objectTerm, "type": target_type})
            edges.append(
                {
                    "id": f"e{item.id}",
                    "source": item.subjectTerm,
                    "target": item.objectTerm,
                    "label": item.axiomType,
                    "type": item.axiomType,
                }
            )
    return {"nodes": list(nodes.values()), "edges": edges}


def build_chart_data(task: OntologyTask, stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "axiomDistribution": [{"name": key, "value": stats[key]} for key in AXIOM_TYPES],
        "classPropertyComparison": [
            {"name": "class", "value": stats["class"]},
            {"name": "property", "value": stats["property"]},
        ],
        "chunkExecution": [
            {"name": "success", "value": task.successCount},
            {"name": "failed", "value": task.failCount},
        ],
    }


def build_turtle(axioms: list[OntologyAxiomResult]) -> str:
    lines = [
        "@prefix : <http://example.org/ontology#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "",
    ]
    for item in axioms:
        s = safe_term(item.subjectTerm)
        o = safe_term(item.objectTerm)
        if item.axiomType == "class":
            lines.append(f":{s} a owl:Class .")
        elif item.axiomType == "property":
            lines.append(f":{s} a owl:ObjectProperty .")
        elif item.axiomType == "subClassOf":
            lines.append(f":{s} rdfs:subClassOf :{o} .")
        elif item.axiomType == "subPropertyOf":
            lines.append(f":{s} rdfs:subPropertyOf :{o} .")
        elif item.axiomType == "domain":
            lines.append(f":{s} rdfs:domain :{o} .")
        elif item.axiomType == "range":
            lines.append(f":{s} rdfs:range :{o} .")
    return "\n".join(lines)


def build_rdfxml(axioms: list[OntologyAxiomResult]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
        '         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"',
        '         xmlns:owl="http://www.w3.org/2002/07/owl#"',
        '         xmlns:ex="http://example.org/ontology#">',
    ]
    for item in axioms:
        s = safe_term(item.subjectTerm)
        o = safe_term(item.objectTerm)
        if item.axiomType == "class":
            lines.append(f'  <owl:Class rdf:about="http://example.org/ontology#{s}" />')
        elif item.axiomType == "property":
            lines.append(f'  <owl:ObjectProperty rdf:about="http://example.org/ontology#{s}" />')
        elif item.axiomType == "subClassOf":
            lines.append(f'  <owl:Class rdf:about="http://example.org/ontology#{s}"><rdfs:subClassOf rdf:resource="http://example.org/ontology#{o}" /></owl:Class>')
        elif item.axiomType in {"subPropertyOf", "domain", "range"}:
            predicate = {"subPropertyOf": "rdfs:subPropertyOf", "domain": "rdfs:domain", "range": "rdfs:range"}[item.axiomType]
            lines.append(f'  <owl:ObjectProperty rdf:about="http://example.org/ontology#{s}"><{predicate} rdf:resource="http://example.org/ontology#{o}" /></owl:ObjectProperty>')
    lines.append("</rdf:RDF>")
    return "\n".join(lines)


def build_owlapi(axioms: list[OntologyAxiomResult]) -> str:
    lines = []
    for item in axioms:
        s = safe_term(item.subjectTerm)
        o = safe_term(item.objectTerm)
        if item.axiomType == "class":
            lines.append(f"Declaration(Class(:{s}))")
        elif item.axiomType == "property":
            lines.append(f"Declaration(ObjectProperty(:{s}))")
        elif item.axiomType == "subClassOf":
            lines.append(f"SubClassOf(:{s} :{o})")
        elif item.axiomType == "subPropertyOf":
            lines.append(f"SubObjectPropertyOf(:{s} :{o})")
        elif item.axiomType == "domain":
            lines.append(f"ObjectPropertyDomain(:{s} :{o})")
        elif item.axiomType == "range":
            lines.append(f"ObjectPropertyRange(:{s} :{o})")
    return "\n".join(lines)


def _load_merged_output(task: OntologyTask) -> dict[str, Any]:
    return _loads(task.mergedOutput or task.outputContent) or {}


def _loads(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def safe_term(value: Optional[str]) -> str:
    text = str(value or "Unnamed").strip()
    text = re.sub(r"[^a-zA-Z0-9_]", "_", text)
    return text or "Unnamed"
