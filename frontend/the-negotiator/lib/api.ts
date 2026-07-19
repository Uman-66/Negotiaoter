import type {
  BackendSpec,
  CallTranscript,
  CompanyCall,
  JobSpec,
  NegotiationProgress,
  QuoteReport,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
// Mocks are now opt-in. Set NEXT_PUBLIC_USE_MOCKS=true only for a visual-only fallback.
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `API ${path} failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function displayCleaningType(value: string) {
  return value === "move_out" ? "Move-out Cleaning" : `${value[0].toUpperCase()}${value.slice(1)} Cleaning`;
}

function toJobSpec(spec: BackendSpec): JobSpec {
  return {
    jobId: spec.id,
    status: spec.confirmed_by_user ? "confirmed" : "ready_for_review",
    cleaningType: displayCleaningType(spec.clean_type),
    houseSizeSqft: spec.property.sqft,
    bedrooms: spec.property.bedrooms,
    bathrooms: spec.property.bathrooms,
    furniture: [],
    specialNotes: spec.open_questions?.join(" ") ?? "",
    sourceFileName: spec.intake_source === "document" ? "uploaded document" : "voice interview",
    backend: spec,
  };
}

function cleanType(value: string): BackendSpec["clean_type"] {
  if (value.toLowerCase().includes("move")) return "move_out";
  if (value.toLowerCase().includes("deep")) return "deep";
  return "standard";
}

function toBackendSpec(spec: JobSpec): Omit<BackendSpec, "id" | "created_at"> {
  const base = spec.backend;
  return {
    property: {
      type: base?.property.type ?? "house",
      sqft: spec.houseSizeSqft,
      bedrooms: spec.bedrooms,
      bathrooms: spec.bathrooms,
      levels: base?.property.levels ?? 1,
    },
    clean_type: cleanType(spec.cleaningType),
    frequency: base?.frequency ?? "one_time",
    condition: base?.condition ?? { clutter_level: "medium", has_pets: false, weeks_since_last_clean: 0 },
    add_ons: base?.add_ons ?? { fridge: false, oven: false, windows: false, baseboards: false, laundry: false },
    access: base?.access ?? { parking: "street", entry_method: "to be confirmed", walk_up_floor: 0 },
    schedule: base?.schedule ?? { preferred_date: "", preferred_time_window: "to be confirmed", flexibility: null },
    open_questions: spec.specialNotes ? [spec.specialNotes] : [],
    confirmed_by_user: base?.confirmed_by_user ?? false,
    intake_source: base?.intake_source ?? "document",
  };
}

function toCompanyCall(call: any): CompanyCall {
  const quote = call.quote;
  const backendStatus = String(call.status ?? "queued");
  const status: CompanyCall["status"] =
    backendStatus === "done" ? "completed" : backendStatus === "queued" ? "waiting" : backendStatus === "declined" ? "declined" : "calling";
  return {
    companyId: call.company_id,
    companyName: call.company_name,
    status,
    price: quote?.final_total ?? quote?.total ?? null,
    extraCharges: quote?.line_items?.map((item: { label: string }) => item.label) ?? [],
    callOutcome: quote?.outcome,
    redFlag: Boolean(quote?.red_flags?.length),
    startedAt: call.updated_at,
    completedAt: status === "completed" ? call.updated_at : undefined,
    notes: quote?.notes,
    transcriptUrl: quote?.transcript_url,
    recordingUrl: quote?.recording_url,
  };
}

export async function uploadJobDocument(file: File): Promise<{ jobId: string }> {
  if (USE_MOCKS) return { jobId: "demo-cleaning-job" };
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/intake/doc`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await response.text());
  const payload = (await response.json()) as { id: string };
  return { jobId: payload.id };
}

export async function getJobSpec(jobId: string): Promise<JobSpec> {
  if (USE_MOCKS) throw new Error("Mock mode has been retired; start the backend or unset NEXT_PUBLIC_USE_MOCKS.");
  return toJobSpec(await http<BackendSpec>(`/specs/${jobId}`));
}

export async function updateJobSpec(jobId: string, patch: Partial<JobSpec>): Promise<JobSpec> {
  const current = await getJobSpec(jobId);
  const next = { ...current, ...patch, jobId };
  const saved = await http<BackendSpec>(`/specs/${jobId}`, {
    method: "PUT",
    body: JSON.stringify(toBackendSpec(next)),
  });
  return toJobSpec(saved);
}

export async function confirmJobSpec(jobId: string): Promise<{ started: boolean }> {
  await http<BackendSpec>(`/specs/${jobId}/confirm`, { method: "PATCH" });
  return { started: true };
}

export async function getNegotiationProgress(jobId: string): Promise<NegotiationProgress> {
  const calls = await http<any[]>(`/calls?spec_id=${encodeURIComponent(jobId)}`);
  const companies = calls.map(toCompanyCall);
  return {
    jobId,
    companies,
    callsCompleted: companies.filter((company) => company.status === "completed" || company.status === "declined").length,
    callsTotal: companies.length,
  };
}

export async function getQuoteReport(jobId: string): Promise<QuoteReport> {
  const [report, progress] = await Promise.all([
    http<any>(`/report/${jobId}`),
    getNegotiationProgress(jobId),
  ]);
  const quotes = report.quotes ?? [];
  const recommended = report.recommended_deal;
  const bestQuote = recommended
    ? {
        companyId: quotes.find((quote: any) => quote.id === recommended.quote_id)?.company_id ?? "",
        companyName: recommended.company_name,
        price: recommended.total,
      }
    : null;
  const prices = progress.companies.map((company) => company.price).filter((price): price is number => price != null);
  return {
    jobId,
    companies: progress.companies,
    bestQuote,
    averagePrice: prices.length ? Math.round(prices.reduce((sum, price) => sum + price, 0) / prices.length) : null,
    warnings: quotes.flatMap((quote: any) => quote.red_flag_reasons ?? []),
  };
}

export async function getCompanyDetail(jobId: string, companyId: string): Promise<CompanyCall> {
  const progress = await getNegotiationProgress(jobId);
  const company = progress.companies.find((item) => item.companyId === companyId);
  if (!company) throw new Error("Company call was not found");
  return company;
}

export async function getCallTranscript(jobId: string, companyId: string): Promise<CallTranscript> {
  const company = await getCompanyDetail(jobId, companyId);
  const lines = [
    { speaker: "agent" as const, text: "Structured call record captured by The Negotiator." },
    { speaker: "company" as const, text: company.callOutcome ? `Outcome: ${company.callOutcome}${company.price != null ? ` — $${company.price}` : ""}.` : "The call is still in progress." },
  ];
  return { companyId, companyName: company.companyName, lines, transcriptUrl: company.transcriptUrl, recordingUrl: company.recordingUrl };
}
