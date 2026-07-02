"use client";

import CytoscapeComponent from "react-cytoscapejs";
import { useMemo, useState } from "react";

export type KnowledgeNodeKind = "meeting" | "decision" | "task" | "person";

export type KnowledgeNode = {
  id: string;
  kind: KnowledgeNodeKind;
  label: string;
};

export type KnowledgeEdgeKind =
  | "meeting_to_decision"
  | "decision_to_task"
  | "task_to_person";

export type KnowledgeEdge = {
  id?: string;
  source: string;
  target: string;
  kind: KnowledgeEdgeKind;
};

export type KnowledgeGraphData = {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
};

export type KnowledgeGraphLayout = "cose" | "breadthfirst";

function nodeColor(kind: KnowledgeNodeKind): string {
  switch (kind) {
    case "meeting":
      return "#60a5fa";
    case "decision":
      return "#a78bfa";
    case "task":
      return "#fbbf24";
    case "person":
      return "#34d399";
  }
}

function edgeColor(kind: KnowledgeEdgeKind): string {
  switch (kind) {
    case "meeting_to_decision":
      return "#38bdf8";
    case "decision_to_task":
      return "#f59e0b";
    case "task_to_person":
      return "#22c55e";
  }
}

function edgeLabel(kind: KnowledgeEdgeKind): string {
  switch (kind) {
    case "meeting_to_decision":
      return "decision";
    case "decision_to_task":
      return "task";
    case "task_to_person":
      return "assigned";
  }
}

export default function KnowledgeGraph({
  data,
  height = "70vh",
  layout = "cose",
  rootId,
  showLegend = true
}: {
  data: KnowledgeGraphData;
  height?: string;
  layout?: KnowledgeGraphLayout;
  rootId?: string;
  showLegend?: boolean;
}) {
  const [selected, setSelected] = useState<
    | { type: "node"; id: string; label: string; kind: KnowledgeNodeKind }
    | { type: "edge"; id: string; kind: KnowledgeEdgeKind; source: string; target: string }
    | null
  >(null);

  const elements = useMemo(
    () => [
      ...data.nodes.map((n) => ({
        data: { id: n.id, label: n.label, kind: n.kind }
      })),
      ...data.edges.map((e, idx) => ({
        data: {
          id: e.id || `e${idx}`,
          source: e.source,
          target: e.target,
          kind: e.kind,
          label: edgeLabel(e.kind)
        }
      }))
    ],
    [data]
  );

  const cyLayout = useMemo(() => {
    if (layout === "breadthfirst") {
      return {
        name: "breadthfirst",
        directed: true,
        padding: 30,
        spacingFactor: 1.25,
        animate: true,
        fit: true,
        ...(rootId ? { roots: `#${cssEscapeId(rootId)}` } : {})
      } as const;
    }
    return { name: "cose", animate: true, fit: true } as const;
  }, [layout, rootId]);

  const stylesheet = useMemo(
    () => [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "font-size": 11,
          "text-wrap": "wrap",
          "text-max-width": 110,
          color: "#e2e8f0",
          "text-outline-color": "#0b1220",
          "text-outline-width": 2,
          "background-color": (ele: any) =>
            nodeColor(ele.data("kind") as KnowledgeNodeKind),
          "border-width": 1,
          "border-color": "rgba(148,163,184,0.25)",
          width: 36,
          height: 36
        }
      },
      {
        selector: 'node[kind = "meeting"]',
        style: { shape: "round-rectangle", width: 120, height: 48, "font-size": 12 }
      },
      {
        selector: 'node[kind = "decision"]',
        style: { shape: "diamond", width: 52, height: 52 }
      },
      {
        selector: 'node[kind = "task"]',
        style: { shape: "round-rectangle", width: 120, height: 44 }
      },
      {
        selector: 'node[kind = "person"]',
        style: { shape: "ellipse", width: 72, height: 36 }
      },
      {
        selector: "edge",
        style: {
          label: "data(label)",
          "font-size": 10,
          color: "rgba(226,232,240,0.85)",
          "text-outline-color": "#0b1220",
          "text-outline-width": 2,
          "line-color": (ele: any) => edgeColor(ele.data("kind") as KnowledgeEdgeKind),
          "target-arrow-color": (ele: any) => edgeColor(ele.data("kind") as KnowledgeEdgeKind),
          "target-arrow-shape": "triangle",
          "arrow-scale": 0.85,
          width: 2,
          "curve-style": "bezier",
          "control-point-step-size": 36
        }
      },
      {
        selector: ":selected",
        style: {
          "border-width": 2,
          "border-color": "rgba(255,255,255,0.7)",
          "line-color": "rgba(255,255,255,0.7)",
          "target-arrow-color": "rgba(255,255,255,0.7)"
        }
      }
    ],
    []
  );

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="text-xs text-slate-400">
          Drag to rearrange • scroll to zoom • click to inspect
        </div>
        {showLegend ? (
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-300">
            <LegendDot color={nodeColor("meeting")} label="Meeting" />
            <LegendDot color={nodeColor("decision")} label="Decision" />
            <LegendDot color={nodeColor("task")} label="Task" />
            <LegendDot color={nodeColor("person")} label="Person" />
          </div>
        ) : null}
      </div>
      <div
        className="w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950/50"
        style={{ height }}
      >
        <CytoscapeComponent
          elements={elements}
          style={{ width: "100%", height: "100%" }}
          layout={cyLayout as any}
          stylesheet={stylesheet as any}
          minZoom={0.35}
          maxZoom={2.25}
          cy={(cy) => {
            cy.on("tap", "node", (evt) => {
              const n = evt.target;
              setSelected({
                type: "node",
                id: n.id(),
                label: n.data("label"),
                kind: n.data("kind")
              });
            });
            cy.on("tap", "edge", (evt) => {
              const e = evt.target;
              setSelected({
                type: "edge",
                id: e.id(),
                kind: e.data("kind"),
                source: e.data("source"),
                target: e.data("target")
              });
            });
            cy.on("tap", (evt) => {
              if (evt.target === cy) setSelected(null);
            });
          }}
        />
      </div>

      {selected ? (
        <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950/50 p-3 text-xs text-slate-200">
          {selected.type === "node" ? (
            <div className="grid gap-1">
              <div className="text-slate-400">Selected node</div>
              <div>
                <span className="font-semibold">{selected.label}</span>{" "}
                <span className="text-slate-400">({selected.kind})</span>
              </div>
              <div className="text-slate-400">id: {selected.id}</div>
            </div>
          ) : (
            <div className="grid gap-1">
              <div className="text-slate-400">Selected edge</div>
              <div>
                <span className="font-semibold">{edgeLabel(selected.kind)}</span>{" "}
                <span className="text-slate-400">({selected.kind})</span>
              </div>
              <div className="text-slate-400">
                {selected.source} → {selected.target}
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-slate-800 bg-slate-950/40 px-2 py-1">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function cssEscapeId(id: string): string {
  // Basic escape for IDs used in selector strings.
  return id.replace(/([ #;?%&,.+*~\':"!^$[\]()=>|\/@])/g, "\\$1");
}

