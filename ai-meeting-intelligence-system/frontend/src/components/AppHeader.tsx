"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { clearAuth, getUserProfile } from "./AuthGate";

function NavLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      className="text-sm text-slate-200 hover:text-white transition"
      href={href}
    >
      {children}
    </Link>
  );
}

export default function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState({ name: "", email: "" });
  const menuRef = useRef<HTMLDivElement | null>(null);

  const hideHeader =
    pathname === "/" || pathname === "/login" || pathname === "/register";

  useEffect(() => {
    setProfile(getUserProfile());
  }, [pathname]);

  useEffect(() => {
    function onDocMouseDown(ev: MouseEvent) {
      if (!open) return;
      const target = ev.target as Node | null;
      if (!target) return;
      if (menuRef.current && !menuRef.current.contains(target)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, [open]);

  function handleLogout() {
    clearAuth();
    setOpen(false);
    router.push("/login");
  }

  const initials = profile.name
    ? profile.name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((p) => p[0]!.toUpperCase())
        .join("")
    : "U";

  return hideHeader ? null : (
    <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/70 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <Link href="/" className="font-semibold tracking-tight">
          AI Meeting Intelligence
        </Link>
        <nav className="flex items-center gap-5">
          <NavLink href="/upload">Upload</NavLink>
          <NavLink href="/meetings">Meetings</NavLink>
          <NavLink href="/ask">Ask</NavLink>
          <NavLink href="/graph">Graph</NavLink>
          <div ref={menuRef} className="relative">
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 bg-slate-950/40 text-sm font-semibold text-slate-100 hover:border-slate-500"
              aria-label="Open profile menu"
            >
              {initials}
            </button>

            {open ? (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-slate-800 bg-slate-900/90 p-4 shadow-lg">
                <div className="text-xs text-slate-400">Signed in user</div>
                <div className="mt-1 text-sm text-slate-100 font-semibold break-words">
                  {profile.name || "User"}
                </div>

                <div className="mt-3 text-xs text-slate-400">Email</div>
                <div className="text-sm text-slate-100 mt-1 break-all">
                  {profile.email || ""}
                </div>

                <button
                  type="button"
                  onClick={handleLogout}
                  className="mt-4 w-full rounded-xl bg-red-500/15 px-3 py-2 text-sm font-semibold text-red-200 hover:bg-red-500/25 border border-red-500/30"
                >
                  Log out
                </button>
              </div>
            ) : null}
          </div>
        </nav>
      </div>
    </header>
  );
}

