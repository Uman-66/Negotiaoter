"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepNav from "@/components/StepNav";
import JSONForm from "@/components/JSONForm";
import { confirmJobSpec, getJobSpec, updateJobSpec } from "@/lib/api";
import type { JobSpec } from "@/lib/types";
import { Loader2 } from "lucide-react";

function ReviewContent() {
  const router = useRouter();
  const params = useSearchParams();
  const jobId = params.get("job");

  const [spec, setSpec] = useState<JobSpec | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    // BACKEND API: GET /job/:jobId
    getJobSpec(jobId).then(setSpec);
  }, [jobId, router]);

  async function handleFieldChange(next: JobSpec) {
    setSpec(next);
    setSaving(true);
    try {
      // BACKEND API: PUT /job/:jobId — persist edits as the user makes them
      await updateJobSpec(next.jobId, next);
    } finally {
      setSaving(false);
    }
  }

  async function handleConfirm() {
    if (!spec) return;
    setConfirming(true);
    try {
      // BACKEND API: POST /job/:jobId/confirm — kicks off the caller agent
      await confirmJobSpec(spec.jobId);
      router.push(`/negotiation?job=${spec.jobId}`);
    } catch {
      setConfirming(false);
    }
  }

  if (!spec) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="animate-spin text-graphite-400" />
      </div>
    );
  }

  return (
    <div className="pb-24">
      <StepNav current="review" />
      <div className="mx-auto max-w-2xl px-6 pt-8">
        <div className="mb-6 flex items-baseline justify-between">
          <div>
            <h1 className="font-display text-2xl font-bold text-ticket sm:text-3xl">
              Confirm the job ticket
            </h1>
            <p className="mt-2 font-body text-sm text-graphite-300">
              We read this from {spec.sourceFileName ?? "your document"}. Fix anything
              before we call companies on your behalf.
            </p>
          </div>
          <span className="font-mono text-xs text-graphite-500">
            {saving ? "Saving..." : "Saved"}
          </span>
        </div>

        <JSONForm spec={spec} onChange={handleFieldChange} />

        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="mt-8 flex w-full items-center justify-center gap-2 rounded-sm bg-amber py-3.5 font-display text-sm font-bold uppercase tracking-wide text-graphite-900 transition disabled:cursor-not-allowed disabled:bg-graphite-500 disabled:text-graphite-300"
        >
          {confirming && <Loader2 size={16} className="animate-spin" />}
          {confirming ? "Starting negotiation..." : "Confirm & start negotiation"}
        </button>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense>
      <ReviewContent />
    </Suspense>
  );
}
