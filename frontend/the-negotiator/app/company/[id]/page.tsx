"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { getCompanyDetail } from "@/lib/api";
import type { CompanyCall } from "@/lib/types";
import { ArrowLeft, Loader2, MessageSquare } from "lucide-react";

function CompanyDetailContent() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const params = useSearchParams();
  const jobId = params.get("job");
  const [company, setCompany] = useState<CompanyCall | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    // BACKEND API: GET /job/:jobId/company/:companyId
    getCompanyDetail(jobId, id).then(setCompany);
  }, [jobId, id, router]);

  if (!company) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="animate-spin text-graphite-400" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-6 pb-24 pt-10">
      <Link
        href={`/report?job=${jobId}`}
        className="mb-6 inline-flex items-center gap-1.5 font-mono text-xs uppercase tracking-widest text-graphite-400 hover:text-amber"
      >
        <ArrowLeft size={14} /> Back to report
      </Link>

      <div className="ticket rounded-sm p-6 sm:p-8">
        <h1 className="font-display text-2xl font-bold text-graphite-900">{company.companyName}</h1>
        {company.phone && <p className="mt-1 font-mono text-xs text-graphite-500">{company.phone}</p>}

        <dl className="mt-6 grid gap-5 sm:grid-cols-2">
          <Detail label="Quoted price" value={company.price != null ? `$${company.price}` : "—"} />
          <Detail label="Cleaning type" value="Deep Cleaning" />
          <Detail label="Travel fee" value={company.travelFee ?? "—"} />
          <Detail
            label="Extra charges"
            value={company.extraCharges?.length ? company.extraCharges.join(", ") : "None"}
          />
          <Detail label="Call outcome" value={company.callOutcome ?? company.status} />
        </dl>

        <Link
          href={`/transcript/${company.companyId}?job=${jobId}`}
          className="mt-8 inline-flex items-center gap-2 rounded-sm border border-graphite-300 px-4 py-2.5 font-mono text-xs uppercase tracking-widest text-graphite-700 transition hover:border-teal hover:text-teal-dark"
        >
          <MessageSquare size={14} /> View call transcript
        </Link>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="font-mono text-[11px] uppercase tracking-widest text-graphite-500">{label}</dt>
      <dd className="mt-1 font-body text-sm text-graphite-800">{value}</dd>
    </div>
  );
}

export default function CompanyDetailPage() {
  return (
    <Suspense>
      <CompanyDetailContent />
    </Suspense>
  );
}
