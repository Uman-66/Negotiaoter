export type JobStatus = "uploaded" | "extracting" | "ready_for_review" | "confirmed" | "negotiating" | "completed";

export interface BackendSpec {
  id: string;
  property: { type: string; sqft: number; bedrooms: number; bathrooms: number; levels: number };
  clean_type: "standard" | "deep" | "move_out";
  frequency: "one_time" | "weekly" | "biweekly" | "monthly";
  condition: { clutter_level: string; has_pets: boolean; weeks_since_last_clean: number };
  add_ons: { fridge: boolean; oven: boolean; windows: boolean; baseboards: boolean; laundry: boolean };
  access: { parking: string; entry_method: string; walk_up_floor: number };
  schedule: { preferred_date: string; preferred_time_window: string; flexibility?: string | null };
  open_questions: string[];
  confirmed_by_user: boolean;
  intake_source: "voice_interview" | "document" | "both";
  created_at?: string;
}

export interface JobSpec {
  jobId: string;
  status: JobStatus;
  cleaningType: string;
  houseSizeSqft: number;
  bedrooms: number;
  bathrooms: number;
  furniture: string[];
  specialNotes: string;
  sourceFileName?: string;
  backend?: BackendSpec;
}

export type CallStatus = "waiting" | "calling" | "completed" | "declined" | "failed";

export interface CompanyCall {
  companyId: string;
  companyName: string;
  phone?: string;
  status: CallStatus;
  price: number | null;
  travelFee?: "included" | "extra" | null;
  extraCharges?: string[];
  callOutcome?: string;
  redFlag?: boolean;
  startedAt?: string;
  completedAt?: string;
  notes?: string;
  transcriptUrl?: string;
  recordingUrl?: string;
}

export interface NegotiationProgress { jobId: string; companies: CompanyCall[]; callsCompleted: number; callsTotal: number; }
export interface QuoteReport { jobId: string; companies: CompanyCall[]; bestQuote: { companyId: string; companyName: string; price: number } | null; averagePrice: number | null; warnings: string[]; }
export interface TranscriptLine { speaker: "agent" | "company"; text: string; timestamp?: string; }
export interface CallTranscript { companyId: string; companyName: string; lines: TranscriptLine[]; transcriptUrl?: string; recordingUrl?: string; }
