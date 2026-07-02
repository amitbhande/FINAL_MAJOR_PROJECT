"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { MeetingListItem } from "@/lib/types";

export default function MeetingsPage() {
  const [items, setItems] = useState<MeetingListItem[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setItems(await apiGet<MeetingListItem[]>("/meetings"));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, []);

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Meetings</h1>
        <p className="mt-1 text-sm text-slate-400">
          Click any meeting to view transcript, summary, and tasks.
        </p>
      </div>

      {err ? (
        <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
          {err}
        </div>
      ) : null}

      <div className="grid gap-3">
        {items.map((m) => (
          <Link
            key={m.id}
            href={`/meetings/${m.id}`}
            className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 hover:border-slate-600 transition"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-semibold">{m.title || "Untitled"}</div>
                <div className="mt-1 text-xs text-slate-400">
                  {new Date(m.created_at).toLocaleString()}
                </div>
              </div>
              <div className="text-xs text-slate-300">
                {m.participants?.length ? `${m.participants.length} ppl` : "—"}
              </div>
            </div>
            {m.participants?.length ? (
              <div className="mt-2 text-xs text-slate-400">
                {m.participants.join(", ")}
              </div>
            ) : null}
          </Link>
        ))}
        {!items.length && !err ? (
          <div className="text-sm text-slate-400">
            No meetings yet. Upload one from the home page.
          </div>
        ) : null}
      </div>
    </div>
  );
}

