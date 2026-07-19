import { ReactNode } from "react";

export default function ReportCard({
  eyebrow,
  value,
  detail,
  icon,
  tone = "default",
}: {
  eyebrow: string;
  value: ReactNode;
  detail?: string;
  icon?: ReactNode;
  tone?: "default" | "warning" | "good";
}) {
  const toneClasses =
    tone === "warning"
      ? "border-signal-red/50 bg-signal-red/5"
      : tone === "good"
      ? "border-signal-green/50 bg-signal-green/5"
      : "border-graphite-500/40";

  return (
    <div className={`ticket flex flex-col gap-1.5 rounded-sm border p-5 ${toneClasses}`}>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-widest text-graphite-500">{eyebrow}</span>
        {icon}
      </div>
      <span className="font-display text-2xl font-bold text-graphite-900">{value}</span>
      {detail && <span className="font-body text-xs text-graphite-500">{detail}</span>}
    </div>
  );
}
