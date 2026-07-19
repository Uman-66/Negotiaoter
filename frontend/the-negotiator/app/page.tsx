import Hero from "@/components/Hero";
import FlowRail from "@/components/FlowRail";
import Link from "next/link";
import { ShieldCheck, Ear, FileCheck2 } from "lucide-react";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <FlowRail />

      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="mb-10 font-display text-sm font-bold uppercase tracking-widest text-graphite-300">
          Built to be honest on the phone
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          <Principle
            icon={<Ear size={18} className="text-teal-light" />}
            title="Discloses it's an agent"
            body="Every call opens by naming who it's calling on behalf of, and answers 'am I talking to a robot?' honestly."
          />
          <Principle
            icon={<ShieldCheck size={18} className="text-teal-light" />}
            title="Never fakes a bid"
            body="Competing quotes are used as real leverage. Inventory and pricing are never invented or misrepresented."
          />
          <Principle
            icon={<FileCheck2 size={18} className="text-teal-light" />}
            title="Ends with a structured outcome"
            body="Every call closes as an itemized quote, a callback commitment, or a documented decline."
          />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="ticket flex flex-col items-start gap-5 rounded-sm p-8 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-display text-xl font-bold text-graphite-900">
              Have a cleaning spec ready?
            </p>
            <p className="mt-1 font-body text-sm text-graphite-600">
              Upload it and we&rsquo;ll have quotes lined up on a report within minutes.
            </p>
          </div>
          <Link
            href="/upload"
            className="whitespace-nowrap rounded-sm bg-graphite-900 px-6 py-3 font-display text-sm font-bold uppercase tracking-wide text-ticket transition hover:bg-graphite-700"
          >
            Get started
          </Link>
        </div>
      </section>
    </>
  );
}

function Principle({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <div className="flex flex-col gap-3 rounded-sm border border-graphite-500/30 p-5">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-graphite-700">
        {icon}
      </span>
      <p className="font-display text-base font-bold text-ticket">{title}</p>
      <p className="font-body text-sm leading-relaxed text-graphite-300">{body}</p>
    </div>
  );
}
