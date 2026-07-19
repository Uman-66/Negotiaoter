"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import CallTimeline from "@/components/CallTimeline";
import { getCallTranscript } from "@/lib/api";
import type { CallTranscript } from "@/lib/types";
import { ArrowLeft, Loader2 } from "lucide-react";

function TranscriptContent() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const params = useSearchParams();
  const jobId = params.get("job");
  const [transcript, setTranscript] = useState<CallTranscript | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    // BACKEND API: GET /job/:jobId/company/:companyId/transcript
    getCallTranscript(jobId, id).then(setTranscript);
  }, [jobId, id, router]);

  if (!transcript) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="animate-spin text-graphite-400" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-6 pb-24 pt-10">
      <Link
        href={`/company/${id}?job=${jobId}`}
        className="mb-6 inline-flex items-center gap-1.5 font-mono text-xs uppercase tracking-widest text-graphite-400 hover:text-amber"
      >
        <ArrowLeft size={14} /> Back to {transcript.companyName}
      </Link>

      <h1 className="mb-6 font-display text-2xl font-bold text-ticket">
        Call transcript &mdash; {transcript.companyName}
      </h1>

      <CallTimeline lines={transcript.lines} />
      {(transcript.transcriptUrl || transcript.recordingUrl) && (
        <div className="mt-6 flex gap-4 font-mono text-xs uppercase tracking-widest text-teal-light">
          {transcript.transcriptUrl && <a href={transcript.transcriptUrl} target="_blank" rel="noreferrer">Open transcript</a>}
          {transcript.recordingUrl && <a href={transcript.recordingUrl} target="_blank" rel="noreferrer">Play recording</a>}
        </div>
      )}
    </div>
  );
}

export default function TranscriptPage() {
  return (
    <Suspense>
      <TranscriptContent />
    </Suspense>
  );
}
