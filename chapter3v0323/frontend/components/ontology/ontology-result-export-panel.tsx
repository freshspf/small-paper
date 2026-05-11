"use client";

import { useEffect, useMemo, useRef, useState, useTransition } from "react";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import * as echarts from "echarts";

import {
  exportOntologyResult,
  getOntologyLayerResults,
  getOntologyResult,
  type OntologyAxiomItem,
  type OntologyExportData,
  type OntologyLayerResults,
  type OntologyResultData,
  type OntologyTaskItem,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


const AXIOM_TYPES = ["all", "class", "property", "subClassOf", "subPropertyOf", "domain", "range"];
const EXPORT_FORMATS = ["json", "ttl", "rdfxml", "owlapi"];


export function OntologyResultExportPanel({ task }: { task: OntologyTaskItem }) {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const distributionChartRef = useRef<HTMLDivElement | null>(null);
  const chunkChartRef = useRef<HTMLDivElement | null>(null);
  const [result, setResult] = useState<OntologyResultData | null>(null);
  const [layerResults, setLayerResults] = useState<OntologyLayerResults | null>(null);
  const [activeTab, setActiveTab] = useState("axioms");
  const [axiomType, setAxiomType] = useState("all");
  const [exportFormat, setExportFormat] = useState("json");
  const [exportData, setExportData] = useState<OntologyExportData | null>(null);
  const [selectedAxiom, setSelectedAxiom] = useState<OntologyAxiomItem | null>(null);
  const [visibleGraphCount, setVisibleGraphCount] = useState(10);
  const [visibleTypes, setVisibleTypes] = useState<Record<string, boolean>>({
    class: true,
    property: true,
    subClassOf: true,
    subPropertyOf: true,
    domain: true,
    range: true,
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setErrorMessage(null);
    startTransition(async () => {
      try {
        const data = await getOntologyResult(task.id, axiomType);
        setResult(data);
        if (task.executionMode === "layered") {
          setLayerResults(await getOntologyLayerResults(task.id));
        } else {
          setLayerResults(null);
        }
        const exportContent = await exportOntologyResult(task.id, exportFormat);
        setExportData(exportContent);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "读取本体结果失败。");
      }
    });
  }, [task.id, task.executionMode, axiomType, exportFormat]);

  useEffect(() => {
    setVisibleGraphCount(10);
  }, [task.id, axiomType]);

  const prioritizedAxioms = useMemo(() => {
    if (!result) {
      return [];
    }
    return prioritizeGraphAxioms(result.axioms);
  }, [result]);

  const graphAxioms = useMemo(() => {
    return prioritizedAxioms.slice(0, visibleGraphCount);
  }, [prioritizedAxioms, visibleGraphCount]);

  const graphElements = useMemo(() => {
    if (!result) {
      return [];
    }
    const allowed = visibleTypes;
    const nodeTypeLookup = new Map(result.graph.nodes.map((node) => [node.id, node.type]));
    const nodeMap = new Map<string, ElementDefinition>();
    const edgeElements: ElementDefinition[] = [];

    for (const axiom of graphAxioms) {
      if (axiom.axiomType === "class" || axiom.axiomType === "property") {
        if (allowed[axiom.axiomType] === false) {
          continue;
        }
        const label = axiom.subjectTerm || axiom.objectTerm || axiom.axiomText || `axiom-${axiom.id}`;
        if (!nodeMap.has(label)) {
          nodeMap.set(label, { data: { id: label, label, type: axiom.axiomType } });
        }
        continue;
      }

      if (allowed[axiom.axiomType] === false) {
        continue;
      }

      const source = axiom.subjectTerm || `subject-${axiom.id}`;
      const target = axiom.objectTerm || `object-${axiom.id}`;
      const sourceType = nodeTypeLookup.get(source) || inferNodeType(axiom.axiomType, "source");
      const targetType = nodeTypeLookup.get(target) || inferNodeType(axiom.axiomType, "target");

      if (!nodeMap.has(source) && allowed[sourceType] !== false) {
        nodeMap.set(source, { data: { id: source, label: source, type: sourceType } });
      }
      if (!nodeMap.has(target) && allowed[targetType] !== false) {
        nodeMap.set(target, { data: { id: target, label: target, type: targetType } });
      }
      if (allowed[sourceType] === false || allowed[targetType] === false) {
        continue;
      }
      edgeElements.push({
        data: {
          id: `edge-${axiom.id}`,
          source,
          target,
          label: axiom.axiomType,
          type: axiom.axiomType,
        },
      });
    }

    return [...nodeMap.values(), ...edgeElements];
  }, [result, graphAxioms, visibleTypes]);

  useEffect(() => {
    if (!graphRef.current) {
      return;
    }
    if (graphElements.length === 0) {
      cyRef.current?.destroy();
      cyRef.current = null;
      return;
    }
    cyRef.current?.destroy();
    const cy = cytoscape({
      container: graphRef.current,
      elements: graphElements,
      layout: { name: "breadthfirst", directed: true, padding: 36, spacingFactor: 1.25 },
      style: [
        {
          selector: "node[type='class']",
          style: {
            label: "data(label)",
            "background-color": "#DBEAFE",
            "border-color": "#2563EB",
            "border-width": 2,
            color: "#1E3A8A",
            shape: "round-rectangle",
            width: "label",
            height: 38,
            padding: "14px",
            "font-size": 11,
            "text-valign": "center",
            "text-halign": "center",
          },
        },
        {
          selector: "node[type='property']",
          style: {
            label: "data(label)",
            "background-color": "#DCFCE7",
            "border-color": "#16A34A",
            "border-width": 2,
            color: "#166534",
            shape: "round-rectangle",
            width: "label",
            height: 38,
            padding: "14px",
            "font-size": 11,
            "text-valign": "center",
            "text-halign": "center",
          },
        },
        edgeStyle("subClassOf", "#2563EB", "solid"),
        edgeStyle("subPropertyOf", "#16A34A", "solid"),
        edgeStyle("domain", "#F97316", "dashed"),
        edgeStyle("range", "#8B5CF6", "dashed"),
        {
          selector: "edge",
          style: {
            label: "data(label)",
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "font-size": 9,
            "text-background-color": "#fff",
            "text-background-opacity": 0.85,
            "text-background-padding": "3px",
          },
        },
        { selector: ".faded", style: { opacity: 0.18 } },
      ],
    });
    cy.on("tap", "node", (event) => {
      const node = event.target;
      cy.elements().addClass("faded");
      node.removeClass("faded");
      node.connectedEdges().removeClass("faded");
      node.connectedEdges().connectedNodes().removeClass("faded");
    });
    cy.on("tap", (event) => {
      if (event.target === cy) {
        cy.elements().removeClass("faded");
      }
    });
    cyRef.current = cy;
    return () => cy.destroy();
  }, [graphElements]);

  useEffect(() => {
    if (!result || !distributionChartRef.current || !chunkChartRef.current) {
      return;
    }
    const distribution = echarts.init(distributionChartRef.current);
    distribution.setOption({
      title: { text: "公理类型分布", left: "center", textStyle: { fontSize: 14 } },
      tooltip: {},
      grid: { left: 70, right: 30, top: 50, bottom: 35 },
      xAxis: { type: "category", data: result.charts.axiomDistribution.map((item) => item.name), axisLabel: { interval: 0, rotate: 25 } },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: result.charts.axiomDistribution.map((item) => item.value), itemStyle: { color: "#8FA8A1", borderRadius: [8, 8, 0, 0] } }],
    });
    const chunk = echarts.init(chunkChartRef.current);
    chunk.setOption({
      title: { text: task.executionMode === "layered" ? "三层/分块执行概况" : "分块执行概况", left: "center", textStyle: { fontSize: 14 } },
      tooltip: {},
      grid: { left: 70, right: 30, top: 50, bottom: 35 },
      xAxis: { type: "category", data: result.charts.chunkExecution.map((item) => item.name) },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: result.charts.chunkExecution.map((item) => item.value), itemStyle: { color: "#D8C3A5", borderRadius: [8, 8, 0, 0] } }],
    });
    return () => {
      distribution.dispose();
      chunk.dispose();
    };
  }, [result, task.executionMode]);

  if (!result) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-ink">结果展示与本体导出</h3>
        <p className="mt-2 text-sm text-slate-500">{isPending ? "正在加载结果..." : errorMessage || "暂无结果。"}</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-ink">结果展示与本体导出</h3>
          <p className="mt-1 text-sm text-slate-600">
            统一展示 baseline 与三层学习的最终聚合本体、结构图、公理列表和多格式导出。
          </p>
        </div>
        <Badge variant="success">{task.executionMode === "layered" ? "三层学习" : "baseline"}</Badge>
      </div>

      <OverviewCards overview={result.overview} />

      <div className="mt-6 space-y-5">
        <div className="rounded-2xl border border-line bg-white/75 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-slate-500">本体结构图</p>
              <p className="mt-1 text-xs text-slate-500">支持缩放、拖拽、节点高亮和 PNG/SVG 导出。初始优先展示关联度更高、彼此有连线的 10 条公理，避免一开始就摊开全部结果。</p>
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => cyRef.current?.layout({ name: "breadthfirst", directed: true, padding: 36, spacingFactor: 1.25 }).run()}>
                重置布局
              </Button>
              <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={exportGraphPng}>
                PNG 视图导出
              </Button>
              <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={exportGraphSvg}>
                SVG
              </Button>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              {["class", "property", "subClassOf", "subPropertyOf", "domain", "range"].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setVisibleTypes((current) => ({ ...current, [type]: !current[type] }))}
                  className={`rounded-full px-3 py-1 text-xs ${visibleTypes[type] ? "bg-sage/15 text-sageDark" : "bg-slate-100 text-slate-400"}`}
                >
                  {type}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500">
                当前展示 {Math.min(graphAxioms.length, result.axioms.length)} / {result.axioms.length} 条公理
              </span>
              <Button
                type="button"
                variant="outline"
                className="px-3 py-2 text-xs"
                onClick={() => setVisibleGraphCount((current) => Math.min(current + 10, result.axioms.length))}
                disabled={graphAxioms.length >= result.axioms.length}
              >
                再显示 10 条
              </Button>
              <Button
                type="button"
                variant="outline"
                className="px-3 py-2 text-xs"
                onClick={() => setVisibleGraphCount(result.axioms.length)}
                disabled={graphAxioms.length >= result.axioms.length}
              >
                全部显示
              </Button>
              <Button
                type="button"
                variant="outline"
                className="px-3 py-2 text-xs"
                onClick={() => setVisibleGraphCount(10)}
                disabled={visibleGraphCount <= 10}
              >
                重置
              </Button>
            </div>
          </div>
          <div className="mt-4 rounded-2xl border border-line bg-[linear-gradient(to_right,#eef1f3_1px,transparent_1px),linear-gradient(to_bottom,#eef1f3_1px,transparent_1px)] bg-[size:32px_32px] p-3">
            <div ref={graphRef} className="h-[760px] rounded-xl bg-white/80" />
          </div>
          <Legend />
        </div>

        <div className="grid gap-5 xl:grid-cols-2">
          <div className="rounded-2xl border border-line bg-white/75 p-4">
            <div ref={distributionChartRef} className="h-[260px]" />
          </div>
          <div className="rounded-2xl border border-line bg-white/75 p-4">
            <div ref={chunkChartRef} className="h-[260px]" />
          </div>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2 border-b border-line pb-3">
        {["axioms", "source", ...(task.executionMode === "layered" ? ["layers"] : []), "export"].map((tab) => (
          <button key={tab} type="button" onClick={() => setActiveTab(tab)} className={`rounded-xl px-4 py-2 text-sm font-medium ${activeTab === tab ? "bg-sage text-white" : "bg-white/70 text-slate-600"}`}>
            {tabLabel(tab)}
          </button>
        ))}
      </div>

      {activeTab === "axioms" ? (
        <AxiomList axioms={result.axioms} axiomType={axiomType} setAxiomType={setAxiomType} onDetail={setSelectedAxiom} />
      ) : null}
      {activeTab === "source" ? (
        <SourcePreview exportFormat={exportFormat} setExportFormat={setExportFormat} exportData={exportData} taskId={task.id} />
      ) : null}
      {activeTab === "layers" && task.executionMode === "layered" ? (
        <LayerResultView layers={layerResults} />
      ) : null}
      {activeTab === "export" ? (
        <ExportCenter taskId={task.id} exportFormat={exportFormat} setExportFormat={setExportFormat} exportData={exportData} onGraphPng={exportGraphPng} onGraphSvg={exportGraphSvg} />
      ) : null}

      {selectedAxiom ? <AxiomDetailDialog axiom={selectedAxiom} onClose={() => setSelectedAxiom(null)} /> : null}
    </Card>
  );

  function exportGraphPng() {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    cy.elements().removeClass("faded");
    const png = cy.png({
      full: false,
      scale: 3.2,
      bg: "#ffffff",
      maxWidth: 1800,
      maxHeight: 1320,
    });
    if (png) {
      downloadDataUrl(png, `ontology_task_${task.id}_${task.executionMode}.png`);
    }
  }

  function exportGraphSvg() {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass("faded");
    const box = cy.elements().boundingBox();
    const padding = 120;
    const titleHeight = 64;
    const legendHeight = 48;
    const viewX = box.x1 - padding;
    const viewY = box.y1 - padding - titleHeight;
    const viewW = Math.max(1100, box.w + padding * 2);
    const viewH = Math.max(760, box.h + padding * 2 + titleHeight + legendHeight);

    const markerDefs = `
      <defs>
        <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#2563EB"/>
        </marker>
        <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#16A34A"/>
        </marker>
        <marker id="arrow-orange" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#F97316"/>
        </marker>
        <marker id="arrow-purple" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#8B5CF6"/>
        </marker>
      </defs>
    `;
    const edges = cy.edges().map((edge) => {
      const s = edge.source().position();
      const t = edge.target().position();
      const type = String(edge.data("type"));
      const color = edgeColor(type);
      const dash = ["domain", "range"].includes(type) ? 'stroke-dasharray="7 5"' : "";
      const marker = {
        subClassOf: "arrow-blue",
        subPropertyOf: "arrow-green",
        domain: "arrow-orange",
        range: "arrow-purple",
      }[type] || "arrow-blue";
      const midX = (s.x + t.x) / 2;
      const midY = (s.y + t.y) / 2 - 8;
      return `
        <line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" stroke="${color}" stroke-width="2.2" ${dash} marker-end="url(#${marker})"/>
        <rect x="${midX - 34}" y="${midY - 11}" width="68" height="18" rx="6" fill="#ffffff" fill-opacity="0.92"/>
        <text x="${midX}" y="${midY + 2}" text-anchor="middle" font-size="9" fill="#475569">${escapeXml(String(edge.data("label")))}</text>
      `;
    }).join("\n");
    const nodes = cy.nodes().map((node) => {
      const p = node.position();
      const label = String(node.data("label"));
      const safeLabel = escapeXml(label);
      const type = String(node.data("type"));
      const fill = type === "property" ? "#DCFCE7" : "#DBEAFE";
      const stroke = type === "property" ? "#16A34A" : "#2563EB";
      const textColor = type === "property" ? "#166534" : "#1E3A8A";
      const width = Math.max(92, Math.min(220, label.length * 8 + 28));
      const height = 38;
      return `
        <rect x="${p.x - width / 2}" y="${p.y - height / 2}" width="${width}" height="${height}" rx="11" fill="${fill}" stroke="${stroke}" stroke-width="2"/>
        <text x="${p.x}" y="${p.y + 4}" text-anchor="middle" font-size="11" font-weight="600" fill="${textColor}">${safeLabel}</text>
      `;
    }).join("\n");
    const title = `
      <text x="${viewX + 12}" y="${viewY + 26}" font-size="20" font-weight="700" fill="#1F2937">Ontology Structure Graph</text>
      <text x="${viewX + 12}" y="${viewY + 46}" font-size="11" fill="#64748B">task #${task.id} · ${task.executionMode === "layered" ? "Layered Learning" : "Baseline"} · ${escapeXml(task.domainType)}</text>
    `;
    const legendY = viewY + viewH - 18;
    const legend = `
      <g>
        ${legendItem(viewX + 16, legendY, "#DBEAFE", "#2563EB", "类节点")}
        ${legendItem(viewX + 150, legendY, "#DCFCE7", "#16A34A", "属性节点")}
        ${legendLineItem(viewX + 284, legendY - 6, "#2563EB", "solid", "subClassOf")}
        ${legendLineItem(viewX + 432, legendY - 6, "#16A34A", "solid", "subPropertyOf")}
        ${legendLineItem(viewX + 610, legendY - 6, "#F97316", "dashed", "domain")}
        ${legendLineItem(viewX + 724, legendY - 6, "#8B5CF6", "dashed", "range")}
      </g>
    `;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${viewW}" height="${viewH}" viewBox="${viewX} ${viewY} ${viewW} ${viewH}">
      <rect width="100%" height="100%" fill="#ffffff"/>
      ${markerDefs}
      ${title}
      ${edges}
      ${nodes}
      ${legend}
    </svg>`;
    downloadText(svg, `ontology_task_${task.id}_${task.executionMode}.svg`, "image/svg+xml");
  }
}

function inferNodeType(axiomType: string, role: "source" | "target") {
  if (axiomType === "subPropertyOf") {
    return "property";
  }
  if (axiomType === "domain" || axiomType === "range") {
    return role === "source" ? "property" : "class";
  }
  return "class";
}

function prioritizeGraphAxioms(axioms: OntologyAxiomItem[]) {
  const typeOrder = ["subClassOf", "subPropertyOf", "domain", "range", "class", "property"];
  const edgeTypes = new Set(["subClassOf", "subPropertyOf", "domain", "range"]);
  const buckets = new Map<string, OntologyAxiomItem[]>();

  for (const type of typeOrder) {
    buckets.set(type, []);
  }
  for (const axiom of axioms) {
    if (!buckets.has(axiom.axiomType)) {
      buckets.set(axiom.axiomType, []);
    }
    buckets.get(axiom.axiomType)!.push(axiom);
  }

  const degreeMap = new Map<string, number>();
  for (const axiom of axioms) {
    if (!edgeTypes.has(axiom.axiomType) || !axiom.subjectTerm || !axiom.objectTerm) {
      continue;
    }
    degreeMap.set(axiom.subjectTerm, (degreeMap.get(axiom.subjectTerm) || 0) + 1);
    degreeMap.set(axiom.objectTerm, (degreeMap.get(axiom.objectTerm) || 0) + 1);
  }

  for (const [type, items] of buckets.entries()) {
    items.sort((a, b) => edgeWeight(b, degreeMap) - edgeWeight(a, degreeMap));
    if (type === "class" || type === "property") {
      items.sort((a, b) => standaloneWeight(b, degreeMap) - standaloneWeight(a, degreeMap));
    }
  }

  const selectedNodes = new Set<string>();
  const selectedIds = new Set<number>();
  const ordered: OntologyAxiomItem[] = [];

  const pushAxiom = (axiom: OntologyAxiomItem | null) => {
    if (!axiom || selectedIds.has(axiom.id)) {
      return;
    }
    ordered.push(axiom);
    selectedIds.add(axiom.id);
    if (axiom.subjectTerm) {
      selectedNodes.add(axiom.subjectTerm);
    }
    if (axiom.objectTerm) {
      selectedNodes.add(axiom.objectTerm);
    }
  };

  // First pass: ensure the initial visible subset covers as many axiom types as possible.
  for (const type of typeOrder) {
    pushAxiom(takeBestAxiom(buckets.get(type) || [], selectedNodes, degreeMap));
  }

  // Second pass: keep expanding by type, but prefer axioms that connect to already shown nodes.
  let progress = true;
  while (progress) {
    progress = false;
    for (const type of typeOrder) {
      const next = takeBestAxiom(buckets.get(type) || [], selectedNodes, degreeMap);
      if (next) {
        pushAxiom(next);
        progress = true;
      }
    }
  }

  for (const axiom of axioms) {
    pushAxiom(axiom);
  }

  return ordered;
}

function edgeWeight(axiom: OntologyAxiomItem, degreeMap: Map<string, number>) {
  const sourceDegree = degreeMap.get(axiom.subjectTerm || "") || 0;
  const targetDegree = degreeMap.get(axiom.objectTerm || "") || 0;
  return sourceDegree + targetDegree;
}

function standaloneWeight(axiom: OntologyAxiomItem, degreeMap: Map<string, number>) {
  const term = axiom.subjectTerm || axiom.objectTerm || "";
  return degreeMap.get(term) || 0;
}

function takeBestAxiom(
  axioms: OntologyAxiomItem[],
  selectedNodes: Set<string>,
  degreeMap: Map<string, number>,
) {
  if (axioms.length === 0) {
    return null;
  }

  if (selectedNodes.size === 0) {
    return axioms.shift() || null;
  }

  let bestIndex = -1;
  let bestScore = -1;

  for (let index = 0; index < axioms.length; index += 1) {
    const axiom = axioms[index];
    const source = axiom.subjectTerm || "";
    const target = axiom.objectTerm || "";
    const sharedCount = Number(selectedNodes.has(source)) + Number(selectedNodes.has(target));
    const score =
      sharedCount * 1000 +
      (axiom.axiomType === "class" || axiom.axiomType === "property"
        ? standaloneWeight(axiom, degreeMap)
        : edgeWeight(axiom, degreeMap));
    if (score > bestScore) {
      bestScore = score;
      bestIndex = index;
    }
  }

  if (bestIndex >= 0) {
    const [axiom] = axioms.splice(bestIndex, 1);
    return axiom;
  }

  return axioms.shift() || null;
}


function edgeStyle(type: string, color: string, lineStyle: "solid" | "dashed") {
  return {
    selector: `edge[type='${type}']`,
    style: { "line-color": color, "target-arrow-color": color, "line-style": lineStyle, color },
  };
}


function OverviewCards({ overview }: { overview: Record<string, number | string | null> }) {
  const cards = [
    ["类数量", overview.class],
    ["属性数量", overview.property],
    ["subClassOf", overview.subClassOf],
    ["subPropertyOf", overview.subPropertyOf],
    ["domain", overview.domain],
    ["range", overview.range],
    ["执行模式", overview.executionMode],
    ["分块", `${overview.successCount ?? 0}/${overview.totalChunkCount ?? 0}`],
  ];
  return (
    <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
      {cards.map(([label, value]) => (
        <div key={label} className="rounded-2xl border border-line bg-white/75 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.16em] text-sageDark/70">{label}</p>
          <p className="mt-2 text-xl font-semibold text-ink">{String(value ?? "--")}</p>
        </div>
      ))}
    </div>
  );
}


function AxiomList({ axioms, axiomType, setAxiomType, onDetail }: { axioms: OntologyAxiomItem[]; axiomType: string; setAxiomType: (type: string) => void; onDetail: (axiom: OntologyAxiomItem) => void }) {
  return (
    <div className="mt-5">
      <div className="mb-3 flex flex-wrap gap-2">
        {AXIOM_TYPES.map((type) => (
          <button key={type} type="button" onClick={() => setAxiomType(type)} className={`rounded-full px-3 py-1 text-xs ${axiomType === type ? "bg-sage text-white" : "bg-white text-slate-600"}`}>
            {type === "all" ? "全部" : type}
          </button>
        ))}
      </div>
      <div className="overflow-hidden rounded-2xl border border-line bg-white/75">
        <div className="overflow-x-auto">
          <table className="paper-table min-w-[980px]">
            <thead>
              <tr>
                <th>编号</th>
                <th>公理类型</th>
                <th>主体术语</th>
                <th>客体术语</th>
                <th>公理文本</th>
                <th>来源层</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {axioms.map((axiom, index) => (
                <tr key={axiom.id}>
                  <td>{index + 1}</td>
                  <td>{axiom.axiomType}</td>
                  <td>{axiom.subjectTerm || "--"}</td>
                  <td>{axiom.objectTerm || "--"}</td>
                  <td><p className="max-w-[360px] truncate">{axiom.axiomText}</p></td>
                  <td>{axiom.sourceLayer}</td>
                  <td><Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => onDetail(axiom)}>详情</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


function SourcePreview({ exportFormat, setExportFormat, exportData, taskId }: { exportFormat: string; setExportFormat: (format: string) => void; exportData: OntologyExportData | null; taskId: number }) {
  return (
    <div className="mt-5">
      <FormatSwitcher value={exportFormat} onChange={setExportFormat} />
      <TextPreview value={exportData?.content || "暂无导出内容"} />
      <div className="mt-3 flex gap-2">
        <Button type="button" variant="outline" onClick={() => copyText(exportData?.content || "")}>复制当前格式</Button>
        <Button type="button" variant="secondary" onClick={() => downloadText(exportData?.content || "", exportData?.filename || `ontology_task_${taskId}.${exportFormat}`, "text/plain")}>下载当前格式</Button>
      </div>
    </div>
  );
}


function ExportCenter({ taskId, exportFormat, setExportFormat, exportData, onGraphPng, onGraphSvg }: { taskId: number; exportFormat: string; setExportFormat: (format: string) => void; exportData: OntologyExportData | null; onGraphPng: () => void; onGraphSvg: () => void }) {
  return (
    <div className="mt-5 rounded-[28px] border border-line bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(244,247,246,0.94))] p-5 shadow-sm">
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-2xl border border-line bg-white/80 p-5">
          <p className="text-sm font-medium text-slate-500">统一文件导出</p>
          <p className="mt-1 text-xs leading-6 text-slate-500">
            用于导出最终本体结果文件。适合论文附录、结果留档和系统演示截图。
          </p>
          <div className="mt-4">
            <FormatSwitcher value={exportFormat} onChange={setExportFormat} />
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <Button type="button" variant="secondary" onClick={() => downloadText(exportData?.content || "", exportData?.filename || `ontology_task_${taskId}.${exportFormat}`, "text/plain")}>
              下载 {exportFormat.toUpperCase()}
            </Button>
            <Button type="button" variant="outline" onClick={() => copyText(exportData?.content || "")}>
              复制当前格式内容
            </Button>
          </div>
          <div className="mt-4 rounded-2xl border border-dashed border-line bg-slate-50 px-4 py-3 text-xs leading-6 text-slate-500">
            当前文件名：{exportData?.filename || `ontology_task_${taskId}.${exportFormat}`}
          </div>
        </div>

        <div className="rounded-2xl border border-line bg-white/80 p-5">
          <p className="text-sm font-medium text-slate-500">本体结构图导出</p>
          <p className="mt-1 text-xs leading-6 text-slate-500">
            图片导出优先保留当前视图构图，适合截图和论文插图。PNG 更偏展示，SVG 更适合后续排版微调。
          </p>
          <div className="mt-5 space-y-3">
            <Button type="button" variant="secondary" className="w-full justify-center" onClick={onGraphPng}>
              导出结构图 PNG（当前视图）
            </Button>
            <Button type="button" variant="outline" className="w-full justify-center" onClick={onGraphSvg}>
              导出结构图 SVG（精排版）
            </Button>
          </div>
          <div className="mt-5 rounded-2xl border border-line bg-[radial-gradient(circle_at_top_left,rgba(143,168,161,0.14),transparent_45%),linear-gradient(180deg,rgba(248,250,252,0.9),rgba(241,245,249,0.9))] px-4 py-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-sageDark/70">导出建议</p>
            <p className="mt-2 text-xs leading-6 text-slate-600">
              先在结构图区域拖到最好看的局部视图，再点 PNG 导出；如果要用于后期排版或 Illustrator 微调，再导出 SVG。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


function LayerResultView({ layers }: { layers: OntologyLayerResults | null }) {
  if (!layers) return <p className="mt-5 text-sm text-slate-500">暂无分层结果。</p>;
  return (
    <div className="mt-5 grid gap-5 lg:grid-cols-3">
      {Object.entries(layers.layers).map(([layer, rows]) => (
        <div key={layer} className="rounded-2xl border border-line bg-white/75 p-4">
          <p className="text-sm font-medium text-slate-500">{formatLayer(layer)}</p>
          <div className="mt-3 max-h-[520px] space-y-3 overflow-auto">
            {rows.map((row) => (
              <div key={row.id} className="rounded-xl border border-line bg-slate-50 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">chunk #{row.chunkRecordId}</span>
                  <Badge variant={row.runStatus === "success" ? "success" : "warning"}>{row.runStatus}</Badge>
                </div>
                <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap text-xs leading-6 text-ink">{row.outputContent || row.errorMessage || "暂无输出"}</pre>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}


function FormatSwitcher({ value, onChange }: { value: string; onChange: (format: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {EXPORT_FORMATS.map((format) => (
        <button key={format} type="button" onClick={() => onChange(format)} className={`rounded-full px-3 py-1 text-xs ${value === format ? "bg-sage text-white" : "bg-white text-slate-600"}`}>
          {format.toUpperCase()}
        </button>
      ))}
    </div>
  );
}


function TextPreview({ value }: { value: string }) {
  return <pre className="mt-4 max-h-[560px] overflow-auto whitespace-pre-wrap rounded-2xl border border-line bg-slate-50 p-4 font-mono text-sm leading-7 text-ink">{value}</pre>;
}


function AxiomDetailDialog({ axiom, onClose }: { axiom: OntologyAxiomItem; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
      <div className="paper-dialog max-w-4xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-semibold text-ink">公理详情</h3>
            <p className="mt-2 text-sm text-slate-600">{axiom.axiomType}</p>
          </div>
          <Button type="button" variant="outline" onClick={onClose}>关闭</Button>
        </div>
        <TextPreview value={JSON.stringify(axiom, null, 2)} />
      </div>
    </div>
  );
}


function Legend() {
  const items = [
    ["类节点", "#2563EB", "solid"],
    ["属性节点", "#16A34A", "solid"],
    ["domain", "#F97316", "dashed"],
    ["range", "#8B5CF6", "dashed"],
  ];
  return (
    <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600">
      {items.map(([label, color, style]) => <span key={label}><span className="mr-1 inline-block h-2 w-6 rounded" style={{ background: color, opacity: style === "dashed" ? 0.55 : 1 }} />{label}</span>)}
    </div>
  );
}


function tabLabel(tab: string) {
  return { axioms: "公理列表", source: "本体源码预览", layers: "分层结果", export: "导出中心" }[tab] ?? tab;
}


function formatLayer(layer: string) {
  return { semantic_network: "语义网络层结果", term_refinement: "术语精化层结果", concept_modeling: "概念建模层结果" }[layer] ?? layer;
}


function edgeColor(type: string) {
  return { subClassOf: "#2563EB", subPropertyOf: "#16A34A", domain: "#F97316", range: "#8B5CF6" }[type] ?? "#64748B";
}


function legendItem(x: number, y: number, fill: string, stroke: string, label: string) {
  return `
    <rect x="${x}" y="${y - 12}" width="34" height="18" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="2"/>
    <text x="${x + 42}" y="${y + 1}" font-size="11" fill="#475569">${label}</text>
  `;
}


function legendLineItem(x: number, y: number, color: string, style: "solid" | "dashed", label: string) {
  const dash = style === "dashed" ? 'stroke-dasharray="7 5"' : "";
  return `
    <line x1="${x}" y1="${y}" x2="${x + 34}" y2="${y}" stroke="${color}" stroke-width="2.2" ${dash}/>
    <text x="${x + 42}" y="${y + 4}" font-size="11" fill="#475569">${label}</text>
  `;
}


function downloadDataUrl(dataUrl: string, filename: string) {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = filename;
  link.click();
}


function downloadText(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  downloadDataUrl(url, filename);
  URL.revokeObjectURL(url);
}


async function copyText(content: string) {
  await navigator.clipboard.writeText(content);
}


function escapeXml(value: string) {
  return value.replace(/[<>&"']/g, (char) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;", "'": "&apos;" }[char] || char));
}
