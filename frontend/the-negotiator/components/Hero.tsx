"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import SwitchboardPanel from "./SwitchboardPanel";

export default function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl gap-12 px-6 pb-20 pt-16 md:grid-cols-[1.1fr_0.9fr] md:pt-24">
      <div className="flex flex-col justify-center">
        <span className="mb-5 inline-flex w-fit items-center gap-2 rounded-full border border-graphite-500/60 px-3 py-1 font-mono text-[11px] uppercase tracking-widest text-teal-light">
          Dispatch desk for home cleaning
        </span>
        <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-tight text-ticket sm:text-5xl md:text-6xl">
          Every quote,
          <br />
          called in.
        </h1>
        <p className="mt-6 max-w-md text-balance font-body text-base leading-relaxed text-graphite-200 sm:text-lg">
          Upload your cleaning job spec once. Our agent works the phones with
          real cleaning companies, negotiates on your behalf, and hands you a
          side-by-side report — no calls for you to make.
        </p>
        <div className="mt-9 flex flex-wrap items-center gap-4">
          <Link
            href="/upload"
            className="group inline-flex items-center gap-2 rounded-sm bg-amber px-6 py-3.5 font-display text-sm font-bold uppercase tracking-wide text-graphite-900 transition hover:bg-amber-light"
          >
            Start a job
            <ArrowRight size={16} className="transition group-hover:translate-x-0.5" />
          </Link>
          <span className="font-mono text-xs text-graphite-400">
            No account needed &mdash; takes about 90 seconds
          </span>
        </div>
      </div>
      <SwitchboardPanel />
    </section>
  );
}
