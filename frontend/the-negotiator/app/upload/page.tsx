"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import StepNav from "@/components/StepNav";
import UploadBox from "@/components/UploadBox";
import { uploadJobDocument } from "@/lib/api";
import { Loader2 } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      // BACKEND API: POST /upload — see lib/api.ts:uploadJobDocument
      const { jobId } = await uploadJobDocument(file);
      router.push(`/processing?job=${jobId}`);
    } catch (e) {
      const detail = e instanceof Error ? e.message : "Please try again.";
      setError(`Upload failed: ${detail}`);
      setSubmitting(false);
    }
  }

  return (
    <div className="pb-24">
      <StepNav current="upload" />
      <div className="mx-auto max-w-xl px-6 pt-8">
        <h1 className="font-display text-2xl font-bold text-ticket sm:text-3xl">
          Upload your cleaning specification
        </h1>
        <p className="mt-2 mb-8 font-body text-sm text-graphite-300">
          A PDF, photo, or scanned document describing the job — rooms, size,
          furniture, anything a cleaning company would need to quote.
        </p>

        <UploadBox
          selectedFile={file}
          onFileSelected={setFile}
          onClear={() => setFile(null)}
        />

        {error && <p className="mt-4 font-body text-sm text-signal-red">{error}</p>}

        <button
          onClick={handleUpload}
          disabled={!file || submitting}
          className="mt-8 flex w-full items-center justify-center gap-2 rounded-sm bg-amber py-3.5 font-display text-sm font-bold uppercase tracking-wide text-graphite-900 transition disabled:cursor-not-allowed disabled:bg-graphite-500 disabled:text-graphite-300"
        >
          {submitting && <Loader2 size={16} className="animate-spin" />}
          {submitting ? "Uploading..." : "Upload & continue"}
        </button>
      </div>
    </div>
  );
}
