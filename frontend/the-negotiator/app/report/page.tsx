"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import StepNav from "@/components/StepNav";
import ReportCard from "@/components/ReportCard";
import QuoteTable from "@/components/QuoteTable";
import { getQuoteReport } from "@/lib/api";
import type { QuoteReport } from "@/lib/types";
import { Loader2, TrendingDown, TrendingUp, AlertTriangle } from "lucide-react";

function ReportContent() {
  const router = useRouter();
  const params = useSearchParams();
  const jobId = params.get("job");
  const [report, setReport] = useState<QuoteReport | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/upload");
      return;
    }
    // BACKEND API: GET /job/:jobId/report (brief refers to this as GET /quotes)
    getQuoteReport(jobId).then(setReport);
  }, [jobId, router]);

  if (!report) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="animate-spin text-graphite-400" />
      </div>
    );
  }

  return (
    <div className="pb-24">
      <StepNav current="report" />
      <div className="mx-auto max-w-4xl px-6 pt-8">
        <h1 className="font-display text-2xl font-bold text-ticket sm:text-3xl">
          Quote report
        </h1>
        <p className="mt-2 mb-8 font-body text-sm text-graphite-300">
          Every call ended with an itemized quote, a callback, or a documented decline.
        </p>

        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <ReportCard
            eyebrow="Best quote"
            value={report.bestQuote ? `$${report.bestQuote.price}` : "—"}
            detail={report.bestQuote?.companyName}
            icon={<TrendingDown size={16} className="text-signal-green" />}
            tone="good"
          />
          <ReportCard
            eyebrow="Average price"
            value={report.averagePrice != null ? `$${report.averagePrice}` : "—"}
            detail={`Across ${report.companies.filter((c) => c.price != null).length} completed calls`}
            icon={<TrendingUp size={16} className="text-teal-light" />}
          />
          <ReportCard
            eyebrow="Flags raised"
            value={report.warnings.length}
            detail={report.warnings.length ? "See warning below" : "Nothing unusual"}
            icon={<AlertTriangle size={16} className={report.warnings.length ? "text-signal-red" : "text-graphite-400"} />}
            tone={report.warnings.length ? "warning" : "default"}
          />
        </div>

        {report.warnings.length > 0 && (
          <div className="mb-8 flex flex-col gap-2">
            {report.warnings.map((w, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-sm border border-signal-red/40 bg-signal-red/5 px-4 py-3 font-body text-sm text-ticket"
              >
                <AlertTriangle size={16} className="mt-0.5 shrink-0 text-signal-red" />
                {w}
              </div>
            ))}
          </div>
        )}

        <QuoteTable
          companies={report.companies}
          jobId={report.jobId}
          bestCompanyId={report.bestQuote?.companyId}
        />
      </div>
    </div>
  );
}

export default function ReportPage() {
  return (
    <Suspense>
      <ReportContent />
    </Suspense>
  );
}
