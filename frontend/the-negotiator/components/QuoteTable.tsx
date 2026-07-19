import Link from "next/link";
import type { CompanyCall } from "@/lib/types";
import { AlertTriangle, ChevronRight } from "lucide-react";

export default function QuoteTable({
  companies,
  jobId,
  bestCompanyId,
}: {
  companies: CompanyCall[];
  jobId: string;
  bestCompanyId?: string;
}) {
  return (
    <div className="overflow-hidden rounded-sm border border-graphite-500/40">
      <table className="w-full border-collapse font-body text-sm">
        <thead>
          <tr className="border-b border-graphite-500/40 bg-graphite-700 text-left font-mono text-[11px] uppercase tracking-widest text-graphite-400">
            <th className="px-5 py-3 font-medium">Company</th>
            <th className="px-5 py-3 font-medium">Price</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="px-5 py-3" />
          </tr>
        </thead>
        <tbody>
          {companies.map((c) => (
            <tr
              key={c.companyId}
              className={`border-b border-graphite-600/60 last:border-0 ${
                c.companyId === bestCompanyId ? "bg-teal/10" : ""
              }`}
            >
              <td className="px-5 py-4">
                <div className="flex items-center gap-2 text-ticket">
                  {c.companyName}
                  {c.companyId === bestCompanyId && (
                    <span className="rounded-full bg-signal-green/20 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-signal-green">
                      Best
                    </span>
                  )}
                  {c.redFlag && (
                    <span title="Below-market red flag">
                      <AlertTriangle size={14} className="text-signal-red" />
                    </span>
                  )}
                </div>
              </td>
              <td className="px-5 py-4 font-tabular text-ticket">
                {c.price != null ? `$${c.price}` : "—"}
              </td>
              <td className="px-5 py-4">
                <span
                  className={`font-mono text-xs uppercase tracking-wide ${
                    c.status === "declined" || c.status === "failed"
                      ? "text-signal-red"
                      : "text-signal-green"
                  }`}
                >
                  {c.status === "completed" ? "Completed" : c.callOutcome ?? c.status}
                </span>
              </td>
              <td className="px-5 py-4 text-right">
                <Link
                  href={`/company/${c.companyId}?job=${jobId}`}
                  className="inline-flex items-center gap-1 font-mono text-xs uppercase tracking-widest text-teal-light hover:text-amber"
                >
                  Details <ChevronRight size={14} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
