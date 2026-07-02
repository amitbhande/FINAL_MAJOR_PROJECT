import dynamic from "next/dynamic";
import Link from "next/link";

import { apiGet } from "@/lib/api";
import type { MeetingOut, TaskTrackerOut } from "@/lib/types";

const DashboardGraphClient = dynamic(() => import("./DashboardGraphClient"), {
  ssr: false
});

function Panel({
  title,
  children
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-base font-semibold">{title}</h2>
      </div>
      <div className="mt-3 text-sm text-slate-200">{children}</div>
    </section>
  );
}

function badgeClass(status: string) {
  return status === "completed"
    ? "border-emerald-900/60 bg-emerald-950/40 text-emerald-200"
    : "border-slate-700 bg-slate-950/50 text-slate-200";
}

export default async function DashboardPage({
  params
}: {
  params: { id: string };
}) {
  const id = params.id;

  let meeting: MeetingOut | null = null;
  let tasks: TaskTrackerOut[] = [];
  let err: string | null = null;

  try {
    meeting = await apiGet<MeetingOut>(`/meetings/${id}`);
    tasks = await apiGet<TaskTrackerOut[]>(`/tasks?meeting_id=${encodeURIComponent(id)}`);
  } catch (e) {
    err = e instanceof Error ? e.message : "Failed to load dashboard";
  }

  if (err) {
    return (
      <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
        {err}
      </div>
    );
  }

  if (!meeting) return null;

  const sentiment = meeting.sentiment || {};

  return (
    <div className="grid gap-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            Dashboard: {meeting.title || "Meeting"}
          </h1>
          <div className="mt-1 text-xs text-slate-400">
            {new Date(meeting.created_at).toLocaleString()} • id: {meeting.id}
          </div>
          {meeting.participants?.length ? (
            <div className="mt-2 text-sm text-slate-300">
              Participants: {meeting.participants.join(", ")}
            </div>
          ) : null}
        </div>
        <div className="flex items-center gap-4 text-sm">
          <Link
            className="text-slate-200 hover:text-white underline underline-offset-4"
            href={`/meetings/${meeting.id}`}
          >
            View meeting
          </Link>
          <Link
            className="text-slate-200 hover:text-white underline underline-offset-4"
            href="/ask"
          >
            Ask (RAG)
          </Link>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="AI summary">
          <div className="whitespace-pre-wrap">{meeting.summary || "—"}</div>
        </Panel>

        <Panel title="Sentiment analysis">
          <div className="grid gap-2">
            <div className="text-xs text-slate-400">Raw</div>
            <pre className="overflow-auto rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs">
              {JSON.stringify(sentiment, null, 2)}
            </pre>
            <div className="text-xs text-slate-400">
              Tip: replace backend sentiment with the richer `analyze_sentiment()` if you
              want label/score/explanation.
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Extracted action items">
          {meeting.action_items?.length ? (
            <ul className="grid gap-2">
              {meeting.action_items.map((ai, idx) => (
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
        </Panel>

        <Panel title="Task tracker">
          {tasks.length ? (
            <div className="grid gap-2">
              {tasks.map((t) => (
                <div
                  key={t.task_id}
                  className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="font-medium">{t.task_name}</div>
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[11px] ${badgeClass(
                        t.status
                      )}`}
                    >
                      {t.status}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    assigned_to: {t.assigned_to || "—"} • deadline:{" "}
                    {t.deadline || "—"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400">
              No tasks in tracker for this meeting yet.
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Meeting transcript">
        <pre className="whitespace-pre-wrap break-words rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-xs leading-relaxed">
          {meeting.transcript_text}
        </pre>
      </Panel>

      <Panel title="Knowledge graph (Meeting → Decision → Task → Person)">
        <DashboardGraphClient meeting={meeting} tasks={tasks} />
      </Panel>
    </div>
  );
}

