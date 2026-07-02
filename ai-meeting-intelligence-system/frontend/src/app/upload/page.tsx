"use client";

import { useMemo, useState } from "react";
import { apiPostForm } from "@/lib/api";
import type { MeetingOut } from "@/lib/types";

function Card({
  title,
  children
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 text-sm text-slate-200">{children}</div>
    </section>
  );
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [participants, setParticipants] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [meeting, setMeeting] = useState<MeetingOut | null>(null);

  const canSubmit = useMemo(() => !!file && !busy, [file, busy]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setErr(null);
    setMeeting(null);
    try {
      const form = new FormData();
      form.append("audio", file);
      if (title.trim()) form.append("title", title.trim());
      if (participants.trim()) form.append("participants", participants.trim());
      const out = await apiPostForm<MeetingOut>("/meetings", form);
      setMeeting(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Upload meeting audio">
        <form className="grid gap-4" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <label className="text-xs text-slate-400">Audio file</label>
            <input
              className="block w-full text-sm file:mr-4 file:rounded-xl file:border-0 file:bg-slate-800 file:px-4 file:py-2 file:text-slate-100 hover:file:bg-slate-700"
              type="file"
              accept="audio/*,video/mp4,video/*,.mp3,.wav,.mp4,.m4a,.aac,.ogg,.webm,.mov,.mkv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <div className="grid gap-2">
            <label className="text-xs text-slate-400">Title (optional)</label>
            <input
              className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Weekly sync"
            />
          </div>

          <div className="grid gap-2">
            <label className="text-xs text-slate-400">
              Participants (comma-separated)
            </label>
            <input
              className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-600"
              value={participants}
              onChange={(e) => setParticipants(e.target.value)}
              placeholder="Anush, Priya, Sam"
            />
          </div>

          <button
            className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            disabled={!canSubmit}
            type="submit"
          >
            {busy ? "Processing…" : "Upload & Analyze"}
          </button>

          {err ? (
            <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
              {err}
            </div>
          ) : null}
        </form>
      </Card>

      <Card title="Result">
        {!meeting ? (
          <div className="text-slate-400">
            Upload an audio file to generate a transcript, summary, action items,
            sentiment, and embeddings.
          </div>
        ) : (
          <div className="grid gap-4">
            <div>
              <div className="text-xs text-slate-400">Meeting</div>
              <div className="font-medium">{meeting.title || "Untitled"}</div>
              <div className="mt-1 text-xs text-slate-400">
                id: <span className="text-slate-200">{meeting.id}</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Transcript (preview)</div>
              <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-200">
                {meeting.transcript_text?.slice(0, 1200) || "—"}
                {(meeting.transcript_text?.length || 0) > 1200 ? "…" : ""}
              </pre>
            </div>
            <div>
              <div className="text-xs text-slate-400">Summary</div>
              <div className="whitespace-pre-wrap">{meeting.summary || "-"}</div>
            </div>
            {meeting.key_points?.length ? (
              <div>
                <div className="text-xs text-slate-400">Key points</div>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {meeting.key_points.map((p, idx) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div>
              <div className="text-xs text-slate-400">Action items</div>
              <ul className="mt-1 grid gap-2">
                {meeting.action_items?.length ? (
                  meeting.action_items.map((ai, idx) => (
                    <li
                      key={idx}
                      className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"
                    >
                      <div className="font-medium">{ai.title}</div>
                      <div className="mt-1 text-xs text-slate-400">
                        owner: {ai.owner || "—"} • due: {ai.due_date || "—"}
                      </div>
                    </li>
                  ))
                ) : (
                  <li className="text-slate-400">No action items found.</li>
                )}
              </ul>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

