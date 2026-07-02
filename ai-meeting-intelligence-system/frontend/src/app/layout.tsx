import "./globals.css";
import AppHeader from "@/components/AppHeader";
import AuthGate from "@/components/AuthGate";
import type { ReactNode } from "react";

export const metadata = {
  title: "AI Meeting Intelligence System",
  description: "Meeting intelligence: transcript, summary, tasks."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthGate>
          <div className="min-h-screen">
            <AppHeader />
            <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          </div>
        </AuthGate>
      </body>
    </html>
  );
}

