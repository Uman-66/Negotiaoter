export default function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const pct = total === 0 ? 0 : Math.round((completed / total) * 100);
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="font-mono text-xs uppercase tracking-widest text-graphite-400">
          Overall
        </span>
        <span className="font-mono text-sm text-ticket">
          {completed} / {total} calls &middot; {pct}%
        </span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-graphite-600">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal to-amber transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
