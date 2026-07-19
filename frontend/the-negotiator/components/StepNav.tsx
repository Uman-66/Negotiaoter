const STEPS = [
  { key: "upload", label: "Upload" },
  { key: "processing", label: "Extract" },
  { key: "review", label: "Confirm" },
  { key: "negotiation", label: "Call" },
  { key: "report", label: "Report" },
];

export default function StepNav({ current }: { current: string }) {
  const currentIndex = STEPS.findIndex((s) => s.key === current);
  return (
    <div className="mx-auto max-w-4xl px-6 pt-10">
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest">
        {STEPS.map((s, i) => (
          <div key={s.key} className="flex items-center gap-2">
            <span
              className={
                i < currentIndex
                  ? "text-signal-green"
                  : i === currentIndex
                  ? "text-amber"
                  : "text-graphite-500"
              }
            >
              {s.label}
            </span>
            {i < STEPS.length - 1 && <span className="text-graphite-600">&rarr;</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
