"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepNav from "@/components/StepNav";
import LoadingAnimation from "@/components/LoadingAnimation";
import { getJobSpec } from "@/lib/api";

function ProcessingContent() {
  const router = useRouter();
  const params = useSearchParams();
  const jobId = params.get("job");
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    let cancelled = false;

    // BACKEND API: GET /job/:jobId — poll until status is "ready_for_review".
    // Swap this setTimeout/poll loop for a WebSocket subscription if the
    // backend offers one for extraction progress.
    async function poll() {
      try {
        const spec = await getJobSpec(jobId as string);
        if (cancelled) return;
        if (spec.status === "ready_for_review" || spec.status === "confirmed") {
          router.push(`/review?job=${jobId}`);
        } else {
          setTimeout(poll, 1500);
        }
      } catch {
        if (!cancelled) setErrored(true);
      }
    }

    const t = setTimeout(poll, 2600); // let the log animation play out
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [jobId, router]);

  return (
    <div className="pb-24">
      <StepNav current="processing" />
      <div className="mx-auto max-w-xl px-6 pt-16 text-center">
        <h1 className="font-display text-2xl font-bold text-ticket sm:text-3xl">
          Analyzing your document...
        </h1>
        <p className="mt-2 mb-10 font-body text-sm text-graphite-300">
          This usually takes a few seconds.
        </p>
        {errored ? (
          <p className="font-body text-sm text-signal-red">
            Something went wrong reading that file. Please go back and try again.
          </p>
        ) : (
          <LoadingAnimation />
        )}
      </div>
    </div>
  );
}

export default function ProcessingPage() {
  return (
    <Suspense>
      <ProcessingContent />
    </Suspense>
  );
}
