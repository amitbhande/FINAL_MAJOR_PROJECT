"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, FormEvent } from "react";
import { setLoggedInFlag, setUserProfile } from "@/components/AuthGate";
import { apiPostJson } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const params = useSearchParams();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = params.get("next") || "/";

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);

    if (!name.trim()) {
      setBusy(false);
      setError("Please enter your name.");
      return;
    }

    const gmailPattern = /^[^@\s]+@gmail\.com$/i;
    if (!gmailPattern.test(email)) {
      setBusy(false);
      setError("Please use a valid Gmail address like username@gmail.com.");
      return;
    }

    if (password.trim().length < 6) {
      setBusy(false);
      setError("Password must be at least 6 characters.");
      return;
    }

    // In a real app you would send this to the backend and store the user.
    // For now we just treat registration as an immediate login.
    setUserProfile({ name: name.trim(), email: email.trim() });
    setLoggedInFlag(true);

    // Record register in MongoDB (fire-and-forget; don't block)
    apiPostJson("/auth/log-login", {
      email: email.trim(),
      name: name.trim(),
      source: "register",
    }).catch(() => {});

    router.push(next);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl">
        <h1 className="text-xl font-semibold text-slate-50">Create account</h1>
        <p className="mt-2 text-xs text-slate-400">
          Sign up with your name, Gmail address, and a password of your choice.
        </p>

        <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
          <div className="grid gap-2">
            <label className="text-xs text-slate-400" htmlFor="name">
              Name
            </label>
            <input
              id="name"
              type="text"
              className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none focus:border-slate-500"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your full name"
              autoComplete="name"
              required
            />
          </div>

          <div className="grid gap-2">
            <label className="text-xs text-slate-400" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none focus:border-slate-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="username@gmail.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="grid gap-2">
            <label className="text-xs text-slate-400" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-50 outline-none focus:border-slate-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="mt-2 rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:opacity-60"
          >
            {busy ? "Creating account…" : "Sign up"}
          </button>

          {error && (
            <div className="rounded-2xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
              {error}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

