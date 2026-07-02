import Link from "next/link";

function ArrowButton() {
  return (
    <span className="group inline-flex items-center justify-center rounded-full border border-slate-700 bg-slate-950/40 px-7 py-4 text-base font-semibold text-slate-100 shadow-[0_0_0_1px_rgba(255,255,255,0.03)] transition hover:border-slate-500 hover:bg-slate-950/70">
      Enter
      <span className="ml-4 inline-flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500 text-white transition group-hover:translate-x-1">
        →
      </span>
    </span>
  );
}

export default function StartPage() {
  return (
    <div className="relative min-h-[calc(100vh-4rem)]">
      <div className="pointer-events-none absolute inset-0 opacity-70">
        <div className="absolute -top-28 -left-28 h-72 w-72 rounded-full bg-indigo-600/25 blur-3xl" />
        <div className="absolute -bottom-28 -right-28 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl" />
      </div>

      <div className="relative mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center justify-center px-4 py-10">
        {/* shapes around the hero box */}
        <div className="pointer-events-none absolute left-[6%] top-[18%] h-28 w-28 rotate-12 rounded-3xl border border-slate-700/50 bg-slate-950/10" />
        <div className="pointer-events-none absolute right-[8%] top-[14%] h-20 w-20 -rotate-6 rounded-full border border-slate-700/50 bg-slate-950/10" />
        <div className="pointer-events-none absolute left-[12%] bottom-[18%] h-16 w-16 -rotate-12 rounded-xl border border-cyan-500/20 bg-cyan-500/5" />
        <div className="pointer-events-none absolute right-[14%] bottom-[16%] h-28 w-28 rotate-45 rounded-3xl border border-indigo-500/20 bg-indigo-500/5" />
        <svg
          className="pointer-events-none absolute left-[2%] top-[52%] h-24 w-24 -rotate-[10deg] opacity-60"
          viewBox="0 0 100 100"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M50 10 L90 85 H10 Z"
            stroke="rgba(148,163,184,0.35)"
            strokeWidth="2"
          />
        </svg>
        <svg
          className="pointer-events-none absolute right-[3%] top-[48%] h-24 w-24 rotate-[14deg] opacity-60"
          viewBox="0 0 100 100"
          fill="none"
          aria-hidden="true"
        >
          <rect
            x="18"
            y="18"
            width="64"
            height="64"
            rx="14"
            stroke="rgba(99,102,241,0.28)"
            strokeWidth="2"
          />
        </svg>

        {/* centered hero box */}
        <div className="relative w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/30 p-10 shadow-[0_0_0_1px_rgba(255,255,255,0.02)] sm:p-14">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -top-24 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-indigo-500/10 blur-2xl" />
          </div>

          <div className="relative">
            <h1 className="text-3xl font-semibold tracking-tight sm:text-5xl">
              AI Meeting Intelligence System
            </h1>
            <p className="mt-4 max-w-2xl text-sm text-slate-300 sm:text-base">
              Turn recordings into actionable notes: transcript, summary, action
              items, sentiment, and tasks.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link href="/upload" aria-label="Go to upload">
                <ArrowButton />
              </Link>
            </div>

            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="text-xs text-slate-400">Capture</div>
                <div className="mt-1 text-sm font-semibold">
                  Recordings → accurate transcript
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="text-xs text-slate-400">Clarity</div>
                <div className="mt-1 text-sm font-semibold">
                  Summary, decisions, and action items
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
                <div className="text-xs text-slate-400">Execution</div>
                <div className="mt-1 text-sm font-semibold">
                  Task tracker + relationship graph
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

