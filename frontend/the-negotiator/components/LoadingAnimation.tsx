"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";

const LOG_LINES = [
  "Reading document...",
  "Extracting rooms...",
  "Extracting furniture...",
  "Estimating square footage...",
  "Drafting job ticket...",
];

export default function LoadingAnimation() {
  const [visible, setVisible] = useState(1);

  useEffect(() => {
    if (visible >= LOG_LINES.length) return;
    const t = setTimeout(() => setVisible((v) => v + 1), 750);
    return () => clearTimeout(t);
  }, [visible]);

  return (
    <div className="ticket mx-auto max-w-md rounded-sm p-6">
      <p className="mb-4 font-mono text-[11px] uppercase tracking-widest text-graphite-500">
        Extraction log
      </p>
      <ul className="flex flex-col gap-3">
        {LOG_LINES.slice(0, visible).map((line, i) => {
          const isLast = i === visible - 1 && visible < LOG_LINES.length + 1;
          const done = i < visible - 1 || visible === LOG_LINES.length;
          return (
            <li key={line} className="flex items-center gap-3 font-body text-sm text-graphite-800 animate-rise">
              {done ? (
                <Check size={15} className="shrink-0 text-signal-green" />
              ) : (
                <Loader2 size={15} className="shrink-0 animate-spin text-teal-dark" />
              )}
              {line}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
