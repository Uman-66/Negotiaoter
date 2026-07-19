import type { TranscriptLine } from "@/lib/types";
import { Bot, Building2 } from "lucide-react";

export default function CallTimeline({ lines }: { lines: TranscriptLine[] }) {
  return (
    <div className="flex flex-col gap-4">
      {lines.map((line, i) => {
        const isAgent = line.speaker === "agent";
        return (
          <div key={i} className={`flex gap-3 ${isAgent ? "" : "flex-row-reverse text-right"}`}>
            <span
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                isAgent ? "bg-teal/20 text-teal-light" : "bg-amber/20 text-amber"
              }`}
            >
              {isAgent ? <Bot size={15} /> : <Building2 size={15} />}
            </span>
            <div
              className={`ticket max-w-md rounded-sm px-4 py-3 ${isAgent ? "" : "bg-ticket"}`}
            >
              <p className="mb-1 font-mono text-[10px] uppercase tracking-widest text-graphite-500">
                {isAgent ? "Agent" : "Company"}
              </p>
              <p className="font-body text-sm leading-relaxed text-graphite-800">{line.text}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
