import { apiGet } from "@/lib/api";
import type { GraphData } from "@/lib/types";
import dynamic from "next/dynamic";

const GraphClient = dynamic(() => import("./GraphClient"), { ssr: false });

export default async function GraphPage() {
  let data: GraphData | null = null;
  let err: string | null = null;
  try {
    data = await apiGet<GraphData>("/graph");
  } catch (e) {
    err = e instanceof Error ? e.message : "Failed to load graph";
  }

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Knowledge Graph</h1>
        <p className="mt-1 text-sm text-slate-400">
          Relationships between meetings, participants, and extracted tasks.
        </p>
      </div>

      {err ? (
        <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
          {err}
        </div>
      ) : null}

      {data ? <GraphClient data={data} /> : null}
    </div>
  );
}

