"use client";

import CytoscapeComponent from "react-cytoscapejs";
import type { GraphData } from "@/lib/types";

function color(kind: string): string {
  if (kind === "meeting") return "#60a5fa";
  if (kind === "person") return "#34d399";
  if (kind === "task") return "#fbbf24";
  return "#a78bfa";
}

export default function GraphClient({ data }: { data: GraphData }) {
  const elements = [
    ...data.nodes.map((n) => ({
      data: { id: n.id, label: n.label, kind: n.kind }
    })),
    ...data.edges.map((e, idx) => ({
      data: { id: `e${idx}`, source: e.source, target: e.target, kind: e.kind }
    }))
  ];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="mb-3 text-xs text-slate-400">
        Tip: drag nodes to rearrange. Zoom/pan with trackpad/mouse.
      </div>
      <div className="h-[70vh] w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950/50">
        <CytoscapeComponent
          elements={elements}
          style={{ width: "100%", height: "100%" }}
          layout={{ name: "cose", animate: true, fit: true }}
          stylesheet={[
            {
              selector: "node",
              style: {
                label: "data(label)",
                "font-size": 10,
                color: "#e2e8f0",
                "text-outline-color": "#0b1220",
                "text-outline-width": 2,
                "background-color": (ele) => color(ele.data("kind")),
                width: 26,
                height: 26
              }
            },
            {
              selector: 'node[kind = "meeting"]',
              style: { shape: "round-rectangle", width: 40, height: 26 }
            },
            {
              selector: "edge",
              style: {
                width: 1,
                "line-color": "#334155",
                "target-arrow-color": "#334155",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier"
              }
            }
          ]}
        />
      </div>
    </div>
  );
}

