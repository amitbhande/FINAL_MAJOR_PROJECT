"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, FormEvent } from "react";
import { getUserProfile, setLoggedInFlag, setUserProfile } from "@/components/AuthGate";
import { apiPostJson } from "@/lib/api";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const next = params.get("next") || "/";

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);

    // Very basic client-side auth:
    // - email must look like something@gmail.com
    // - password must be at least 6 characters
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

    // If checks pass, consider the user logged in.
    const current = getUserProfile();
    const derivedName =
      current.name ||
      email
        .split("@")[0]
        .replace(/[._-]+/g, " ")
        .trim()
        .replace(/\b\w/g, (c) => c.toUpperCase());
    setUserProfile({ name: derivedName || "User", email });
    setLoggedInFlag(true);

    // Record login in MongoDB (fire-and-forget; don't block login)
    apiPostJson("/auth/log-login", {
      email: email.trim(),
      name: derivedName || "User",
      source: "login",
    }).catch(() => {});

    router.push(next);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl">
        <h1 className="text-xl font-semibold text-slate-50">Sign in</h1>
        <p className="mt-2 text-xs text-slate-400">
          Use any{" "}
          <span className="font-mono">username@gmail.com</span> and a password
          of your choice (min. 6 characters).
        </p>

        <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
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
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="mt-2 rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
            <Link
              href="/register"
              className="text-indigo-400 hover:text-indigo-300"
            >
              Create an account
            </Link>
            <Link
              href="#"
              onClick={(e) => {
                e.preventDefault();
                // Basic UX for now; real app would trigger reset flow.
                alert("Password reset is not wired to a backend yet.");
              }}
              className="text-slate-400 hover:text-slate-200"
            >
              Forgot password?
            </Link>
          </div>

          {error && (
            <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
              {error}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

