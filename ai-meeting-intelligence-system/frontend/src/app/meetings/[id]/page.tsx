"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { MeetingOut } from "@/lib/types";

function Section({
  title,
  children
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
      <h2 className="text-base font-semibold">{title}</h2>
      <div className="mt-3 text-sm text-slate-200">{children}</div>
    </section>
  );
}

export default function MeetingDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [m, setM] = useState<MeetingOut | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setM(await apiGet<MeetingOut>(`/meetings/${id}`));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
  }, [id]);

  if (err) {
    return (
      <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
        {err}
      </div>
    );
  }

  if (!m) return <div className="text-sm text-slate-400">Loading…</div>;

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">{m.title || "Untitled"}</h1>
        <div className="mt-1 text-xs text-slate-400">
          {new Date(m.created_at).toLocaleString()} • id: {m.id}
        </div>
        {m.participants?.length ? (
          <div className="mt-2 text-sm text-slate-300">
            Participants: {m.participants.join(", ")}
          </div>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Summary">
          <div className="whitespace-pre-wrap">{m.summary || "—"}</div>
        </Section>
        <Section title="Key points">
          {m.key_points?.length ? (
            <ul className="list-disc space-y-1 pl-5">
              {m.key_points.map((p, idx) => (
                <li key={idx}>{p}</li>
              ))}
            </ul>
          ) : (
            <div className="text-slate-400">—</div>
          )}
        </Section>
        <Section title="Action items">
          {m.action_items?.length ? (
            <ul className="grid gap-2">
              {m.action_items.map((ai, idx) => (
                <li
                  key={idx}
                  className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"
                >
                  <div className="font-medium">{ai.title}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    owner: {ai.owner || "—"} • due: {ai.due_date || "—"} •{" "}
                    {ai.status}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-slate-400">No action items found.</div>
          )}
        </Section>
      </div>

      {m.speaker_segments && m.speaker_segments.length > 0 ? (
        <Section title="Transcript by speaker">
          <p className="mb-3 text-xs text-slate-400">
            Speaker labels use your participant order when possible; otherwise
            &quot;Speaker 1&quot;, &quot;Speaker 2&quot;, … (diarization is approximate).
          </p>
          <ul className="grid gap-3">
            {m.speaker_segments.map((seg, idx) => (
              <li
                key={idx}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-xs leading-relaxed"
              >
                <div className="mb-1 font-semibold text-slate-100">{seg.speaker}</div>
                <div className="whitespace-pre-wrap text-slate-200">{seg.text}</div>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <Section title="Transcript (full text)">
        <pre className="whitespace-pre-wrap break-words rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-xs leading-relaxed">
          {m.transcript_text}
        </pre>
      </Section>
    </div>
  );
}

