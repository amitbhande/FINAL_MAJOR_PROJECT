"use client";

import { useMemo, useState } from "react";
import { apiPostJson } from "@/lib/api";
import type { AskResponse } from "@/lib/types";

export default function AskPage() {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [resp, setResp] = useState<AskResponse | null>(null);

  const canAsk = useMemo(() => q.trim().length > 3 && !busy, [q, busy]);

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    const question = q.trim();
    if (!question) return;
    setBusy(true);
    setErr(null);
    setResp(null);
    try {
      const out = await apiPostJson<AskResponse>("/meetings/ask", {
        question,
        top_k: 6
      });
      setResp(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Ask past meetings (RAG)</h1>
        <p className="mt-1 text-sm text-slate-400">
          Queries are answered using retrieved transcript chunks from ChromaDB.
        </p>
      </div>

      <form onSubmit={onAsk} className="grid gap-3">
        <textarea
          className="min-h-28 rounded-2xl border border-slate-800 bg-slate-950 p-4 text-sm outline-none focus:border-slate-600"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="What did we decide about the launch date?"
        />
        <div className="flex items-center gap-3">
          <button
            disabled={!canAsk}
            className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            type="submit"
          >
            {busy ? "Thinking…" : "Ask"}
          </button>
          {err ? <div className="text-xs text-red-200">{err}</div> : null}
        </div>
      </form>

      {resp ? (
        <div className="grid gap-4">
          <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="text-base font-semibold">Answer</h2>
            <div className="mt-3 whitespace-pre-wrap text-sm text-slate-200">
              {resp.answer || "(No answer returned — configure LLM env vars.)"}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <h2 className="text-base font-semibold">Sources</h2>
            <div className="mt-3 grid gap-3">
              {resp.sources?.length ? (
                resp.sources.map((s) => (
                  <div
                    key={s.id}
                    className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"
                  >
                    <div className="text-xs text-slate-400">
                      meeting_id:{" "}
                      <span className="text-slate-200">{s.meeting_id}</span> •
                      chunk: {s.chunk_index} • distance:{" "}
                      {typeof s.distance === "number"
                        ? s.distance.toFixed(4)
                        : "—"}
                    </div>
                    <div className="mt-2 whitespace-pre-wrap text-xs text-slate-200">
                      {s.chunk}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-400">
                  No sources returned.
                </div>
              )}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

