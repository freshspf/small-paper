"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


const ONTOLOGY_ELEMENTS: ElementDefinition[] = [
  { data: { id: "Thing", label: "Thing", type: "Class" } },
  { data: { id: "Person", label: "Person", type: "Class" } },
  { data: { id: "Artist", label: "Artist", type: "Class" } },
  { data: { id: "Musician", label: "Musician", type: "Class" } },
  { data: { id: "Writer", label: "Writer", type: "Class" } },
  { data: { id: "CreativeWork", label: "CreativeWork", type: "Class" } },
  { data: { id: "MusicalWork", label: "MusicalWork", type: "Class" } },
  { data: { id: "Album", label: "Album", type: "Class" } },
  { data: { id: "Place", label: "Place", type: "Class" } },
  { data: { id: "City", label: "City", type: "Class" } },

  { data: { id: "e1", source: "Person", target: "Thing", label: "subClassOf" } },
  { data: { id: "e2", source: "Artist", target: "Person", label: "subClassOf" } },
  { data: { id: "e3", source: "Musician", target: "Artist", label: "subClassOf" } },
  { data: { id: "e4", source: "Writer", target: "Artist", label: "subClassOf" } },
  { data: { id: "e5", source: "CreativeWork", target: "Thing", label: "subClassOf" } },
  { data: { id: "e6", source: "MusicalWork", target: "CreativeWork", label: "subClassOf" } },
  { data: { id: "e7", source: "Album", target: "MusicalWork", label: "subClassOf" } },
  { data: { id: "e8", source: "Place", target: "Thing", label: "subClassOf" } },
  { data: { id: "e9", source: "City", target: "Place", label: "subClassOf" } },
];


export function OntologyPanel() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState("Album");

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: ONTOLOGY_ELEMENTS,
      layout: {
        name: "breadthfirst",
        directed: true,
        padding: 24,
        spacingFactor: 1.1,
      },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            width: "64",
            height: "64",
            "background-color": "#8FA8A1",
            color: "#ffffff",
            "font-size": "12",
            "font-weight": "bold",
            "text-wrap": "wrap",
            "text-max-width": "80",
            "text-valign": "center",
            "text-halign": "center",
            "border-width": "2",
            "border-color": "#4F5B58",
          },
        },
        {
          selector: "node:selected",
          style: {
            "background-color": "#D8C3A5",
            "border-color": "#8C7B6A",
            color: "#4F3F34",
          },
        },
        {
          selector: "edge",
          style: {
            width: "2",
            "line-color": "#94A3B8",
            "target-arrow-color": "#94A3B8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": "10",
            color: "#64748B",
            "text-background-color": "#ffffff",
            "text-background-opacity": 0.9,
            "text-background-padding": "3",
          },
        },
      ],
    });

    cy.on("tap", "node", (event) => {
      const nodeId = event.target.id();
      setSelectedNodeId(nodeId);
    });

    const initialNode = cy.getElementById(selectedNodeId);
    if (initialNode.length > 0) {
      initialNode.select();
      cy.center(initialNode);
    }

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, []);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }

    cy.elements().unselect();
    const node = cy.getElementById(selectedNodeId);
    if (node.length > 0) {
      node.select();
    }
  }, [selectedNodeId]);

  const selectedInfo = useMemo(() => {
    const outgoing = ONTOLOGY_ELEMENTS.filter(
      (item) => item.data?.source === selectedNodeId,
    ).map((item) => item.data?.target as string);
    const incoming = ONTOLOGY_ELEMENTS.filter(
      (item) => item.data?.target === selectedNodeId,
    ).map((item) => item.data?.source as string);

    return {
      label: selectedNodeId,
      parent: outgoing[0] ?? "无",
      children: incoming,
    };
  }, [selectedNodeId]);

  function zoomIn() {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    cy.zoom({
      level: cy.zoom() * 1.15,
      renderedPosition: { x: 320, y: 240 },
    });
  }

  function zoomOut() {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    cy.zoom({
      level: cy.zoom() * 0.85,
      renderedPosition: { x: 320, y: 240 },
    });
  }

  function resetView() {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    cy.fit(undefined, 40);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">本体图谱画布</h3>
            <p className="text-sm text-slate-600">
              使用 Cytoscape.js 展示静态演示数据中的类层次结构，仅包含 subClassOf 关系。
            </p>
          </div>
          <div className="flex gap-2">
            <Badge>subClassOf</Badge>
            <Badge variant="muted">静态演示数据</Badge>
          </div>
        </div>

        <div className="mt-6 rounded-[28px] border border-line bg-[radial-gradient(circle_at_top_left,#f8fafc,transparent_35%),linear-gradient(to_right,#eef1f3_1px,transparent_1px),linear-gradient(to_bottom,#eef1f3_1px,transparent_1px)] bg-[size:auto,36px_36px,36px_36px] p-4">
          <div ref={containerRef} className="h-[560px] w-full rounded-[22px] bg-white/70" />
        </div>
      </Card>

      <div className="space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-ink">节点详情</h3>
            <Badge variant="success">当前选中</Badge>
          </div>
          <div className="mt-5 space-y-4">
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-sageDark/80">类名称</p>
              <p className="mt-2 text-sm font-medium text-ink">{selectedInfo.label}</p>
            </div>
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-sageDark/80">父类</p>
              <p className="mt-2 text-sm font-medium text-ink">{selectedInfo.parent}</p>
            </div>
            <div className="rounded-xl border border-line bg-white/70 p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-sageDark/80">子类</p>
              <p className="mt-2 text-sm font-medium text-ink">
                {selectedInfo.children.length > 0 ? selectedInfo.children.join(", ") : "无"}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-ink">图谱控制</h3>
          <div className="mt-5 grid gap-3">
            <Button variant="outline" className="justify-start" onClick={zoomIn}>
              放大视图
            </Button>
            <Button variant="outline" className="justify-start" onClick={zoomOut}>
              缩小视图
            </Button>
            <Button variant="outline" className="justify-start" onClick={resetView}>
              重置布局
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-ink">说明</h3>
          <div className="mt-5 space-y-4 text-sm leading-7 text-slate-600">
            <p>
              该页面用于展示本体类层次与关系结构，本阶段采用静态类层次数据，不直接连接真实本体库或 SPARQL 服务。
            </p>
            <p>
              后续若接入 Fuseki，可将当前 Cytoscape.js 画布替换为基于 RDF 查询结果的动态图谱视图。
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
