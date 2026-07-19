"use client";

import { useEffect, useState } from "react";

const LINES = [
  { id: "L1", name: "ABC Cleaning" },
  { id: "L2", name: "Spark Clean" },
  { id: "L3", name: "Fresh Home" },
  { id: "L4", name: "Home Care Co." },
  { id: "L5", name: "Bright Nest" },
  { id: "L6", name: "Home Care Co." },
];

type LampState = "idle" | "ringing" | "connected" | "done";

const STATE_COLOR: Record<LampState, string> = {
  idle: "bg-graphite-500",
  ringing: "bg-amber",
  connected: "bg-teal-light",
  done: "bg-signal-green",
};

export default function SwitchboardPanel() {
  const [states, setStates] = useState<LampState[]>(LINES.map(() => "idle"));

  useEffect(() => {
    let tick = 0;
    const interval = setInterval(() => {
      tick += 1;
      setStates((prev) =>
        prev.map((_, i) => {
          const phase = (tick + i * 2) % 8;
          if (phase < 2) return "idle";
          if (phase < 4) return "ringing";
          if (phase < 6) return "connected";
          return "done";
        })
      );
    }, 650);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ticket flex flex-col gap-3 self-start rounded-sm p-5 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.6)]">
      <div className="flex items-center justify-between border-b border-graphite-300/40 pb-3">
        <span className="font-mono text-[11px] uppercase tracking-widest text-graphite-500">
          Patch panel &mdash; live
        </span>
        <span className="font-mono text-[11px] text-graphite-500">6 lines</span>
      </div>
      <div className="flex flex-col divide-y divide-graphite-300/30">
        {LINES.map((line, i) => (
          <div key={line.id + i} className="flex items-center justify-between py-2.5">
            <div className="flex items-center gap-3">
              <span
                className={`signal-lamp ${STATE_COLOR[states[i]]} ${
                  states[i] === "ringing" ? "animate-blink" : ""
                }`}
              />
              <span className="font-mono text-xs text-graphite-700">{line.id}</span>
              <span className="font-body text-sm text-graphite-800">{line.name}</span>
            </div>
            <span className="font-mono text-[11px] uppercase tracking-wide text-graphite-500">
              {states[i]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
