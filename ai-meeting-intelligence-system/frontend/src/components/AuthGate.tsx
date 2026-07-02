"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

const STORAGE_KEY = "aimis_logged_in";
const STORAGE_KEY_NAME = "aimis_user_name";
const STORAGE_KEY_EMAIL = "aimis_user_email";

export function setLoggedInFlag(value: boolean) {
  if (typeof window === "undefined") return;
  if (value) {
    window.localStorage.setItem(STORAGE_KEY, "1");
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function setUserProfile(profile: { name: string; email: string }) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY_NAME, profile.name);
  window.localStorage.setItem(STORAGE_KEY_EMAIL, profile.email);
}

export function getUserProfile() {
  if (typeof window === "undefined") {
    return { name: "", email: "" };
  }
  return {
    name: window.localStorage.getItem(STORAGE_KEY_NAME) || "",
    email: window.localStorage.getItem(STORAGE_KEY_EMAIL) || ""
  };
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.localStorage.removeItem(STORAGE_KEY_NAME);
  window.localStorage.removeItem(STORAGE_KEY_EMAIL);
}

function isLoggedIn() {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(STORAGE_KEY) === "1";
}

export default function AuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    // Public routes that do not require auth
    if (pathname === "/login" || pathname === "/register") {
      setReady(true);
      setAuthed(false);
      return;
    }

    const ok = isLoggedIn();
    if (!ok) {
      router.replace("/login");
      return;
    }

    setAuthed(true);
    setReady(true);
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 px-6 py-4 text-sm">
          Checking session…
        </div>
      </div>
    );
  }

  if (!authed && pathname !== "/login" && pathname !== "/register") {
    // Redirect in progress
    return null;
  }

  return <>{children}</>;
}

