"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepNav from "@/components/StepNav";
import ProgressBar from "@/components/ProgressBar";
import CompanyCard from "@/components/CompanyCard";
import { getNegotiationProgress } from "@/lib/api";
import type { NegotiationProgress } from "@/lib/types";
import { Loader2 } from "lucide-react";

function NegotiationContent() {
  const router = useRouter();
  const params = useSearchParams();
  const jobId = params.get("job");
  const [progress, setProgress] = useState<NegotiationProgress | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    let cancelled = false;

    // BACKEND API: GET /job/:jobId/negotiation — poll every ~2s.
    // Replace with a WebSocket/Socket.io subscription for true real-time
    // updates; see the note at the bottom of lib/api.ts.
    async function poll() {
      const data = await getNegotiationProgress(jobId as string);
      if (cancelled) return;
      setProgress(data);
      if (data.callsCompleted >= data.callsTotal) {
        setTimeout(() => router.push(`/report?job=${jobId}`), 1200);
      } else {
        setTimeout(poll, 2000);
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, [jobId, router]);

  if (!progress) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="animate-spin text-graphite-400" />
      </div>
    );
  }

  return (
    <div className="pb-24">
      <StepNav current="negotiation" />
      <div className="mx-auto max-w-2xl px-6 pt-8">
        <h1 className="font-display text-2xl font-bold text-ticket sm:text-3xl">
          Negotiation in progress
        </h1>
        <p className="mt-2 mb-8 font-body text-sm text-graphite-300">
          Sit tight — we&rsquo;re calling each company and negotiating a quote.
        </p>

        <div className="mb-8">
          <ProgressBar completed={progress.callsCompleted} total={progress.callsTotal} />
        </div>

        <div className="flex flex-col gap-3">
          {progress.companies.map((c) => (
            <CompanyCard key={c.companyId} company={c} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function NegotiationPage() {
  return (
    <Suspense>
      <NegotiationContent />
    </Suspense>
  );
}
