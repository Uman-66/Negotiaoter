"use client";

import Link from "next/link";
import { PhoneCall } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-graphite-500/40 bg-graphite-800/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2.5 font-display text-lg font-bold tracking-tight text-ticket">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-graphite-600">
            <PhoneCall size={14} className="text-amber" />
          </span>
          The Negotiator
        </Link>
        <nav className="hidden items-center gap-6 font-mono text-xs uppercase tracking-widest text-graphite-300 sm:flex">
          <span className="flex items-center gap-1.5">
            <span className="signal-lamp bg-signal-green text-signal-green animate-blink" />
            Lines open
          </span>
          <Link href="/upload" className="transition hover:text-amber">
            Start a job
          </Link>
        </nav>
      </div>
    </header>
  );
}
