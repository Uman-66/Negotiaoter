import type { CompanyCall } from "@/lib/types";
import { Phone, PhoneOff, Clock, CheckCircle2 } from "lucide-react";

const STATUS_META: Record<CompanyCall["status"], { label: string; color: string; icon: JSX.Element }> = {
  waiting: { label: "Waiting", color: "text-graphite-400", icon: <Clock size={15} /> },
  calling: { label: "Calling...", color: "text-amber", icon: <Phone size={15} className="animate-blink" /> },
  completed: { label: "Completed", color: "text-signal-green", icon: <CheckCircle2 size={15} /> },
  declined: { label: "Declined", color: "text-signal-red", icon: <PhoneOff size={15} /> },
  failed: { label: "No answer", color: "text-signal-red", icon: <PhoneOff size={15} /> },
};

export default function CompanyCard({ company }: { company: CompanyCall }) {
  const meta = STATUS_META[company.status];
  return (
    <div className="ticket flex items-center justify-between rounded-sm px-5 py-4">
      <div className="flex items-center gap-3">
        <span
          className={`signal-lamp ${
            company.status === "completed"
              ? "bg-signal-green text-signal-green"
              : company.status === "calling"
              ? "bg-amber text-amber animate-blink"
              : company.status === "declined" || company.status === "failed"
              ? "bg-signal-red text-signal-red"
              : "bg-graphite-300 text-graphite-300"
          }`}
        />
        <span className="font-body text-sm font-medium text-graphite-800">{company.companyName}</span>
      </div>
      <span className={`flex items-center gap-1.5 font-mono text-xs uppercase tracking-wide ${meta.color}`}>
        {meta.icon}
        {meta.label}
        {company.price != null && (
          <span className="ml-1 font-tabular text-graphite-800">${company.price}</span>
        )}
      </span>
    </div>
  );
}
