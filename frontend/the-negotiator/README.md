# The Negotiator — Frontend

Frontend for **The Negotiator**: user uploads a cleaning job spec, an AI agent
calls cleaning companies and negotiates, and the user gets a comparison
report. This repo is the frontend only — no AI agents, Twilio, or ElevenLabs
live here. It consumes whatever API the backend team ships.

Built with **Next.js 15 (App Router) + TypeScript + Tailwind CSS**.

## Running it

```bash
npm install
npm run dev
```

Open http://localhost:3000. The app runs immediately with realistic **mock
data** — you don't need the backend to demo or build against this.

## Where the backend plugs in

**Everything lives in one file: [`lib/api.ts`](./lib/api.ts).** No page or
component calls `fetch` directly — they all import functions from there. When
the backend team hands you real endpoints:

1. Copy `.env.local.example` to `.env.local`.
2. Set `NEXT_PUBLIC_API_BASE_URL` to their base URL.
3. Set `NEXT_PUBLIC_USE_MOCKS=false`.
4. Open `lib/api.ts` — every exported function already has the real `fetch`
   call written next to its mock, marked with a `// BACKEND CALL` comment.
   Adjust the path/payload shape to match whatever the backend actually
   returns, and delete the mock line beneath it.

| Function | Endpoint (as briefed) | Used on |
|---|---|---|
| `uploadJobDocument` | `POST /upload` (multipart, field `file`) → `{ jobId }` | Upload page |
| `getJobSpec` | `GET /job/:jobId` → job spec JSON | Processing page (poll), Review page |
| `updateJobSpec` | `PUT /job/:jobId` | Review page (on edit) |
| `confirmJobSpec` | `POST /job/:jobId/confirm` | Review page ("Confirm & start negotiation") |
| `getNegotiationProgress` | `GET /job/:jobId/negotiation` (poll, or swap for a socket) | Negotiation Progress page |
| `getQuoteReport` | `GET /job/:jobId/report` (briefed as `GET /quotes`) | Report Dashboard |
| `getCompanyDetail` | `GET /job/:jobId/company/:companyId` | Company Details page |
| `getCallTranscript` | `GET /job/:jobId/company/:companyId/transcript` | Call Transcript page (optional) |

All shared TypeScript shapes (`JobSpec`, `CompanyCall`, `NegotiationProgress`,
`QuoteReport`, `CallTranscript`) are defined once in `lib/types.ts` — if the
backend's JSON differs, that's the other file to edit.

If the backend offers a **WebSocket/Socket.io** channel for live negotiation
progress instead of a polling endpoint, there's a stub at the bottom of
`lib/api.ts` showing exactly where to swap it in on the Negotiation page.

## Pages (matches the user flow in the brief)

```
/                     Landing page
/upload               Upload PDF / image / doc
/processing           "Analyzing your document..." (polls job status)
/review               Review & confirm the extracted job ticket, edit fields
/negotiation           Live call-by-call progress
/report               Comparison dashboard: best quote, average, red flags
/company/[id]         One company's quote in detail
/transcript/[id]      Call transcript (optional, judges tend to like this)
```

## Structure

```
app/
  page.tsx                  Landing
  upload/page.tsx
  processing/page.tsx
  review/page.tsx
  negotiation/page.tsx
  report/page.tsx
  company/[id]/page.tsx
  transcript/[id]/page.tsx
  layout.tsx, globals.css
components/
  Navbar.tsx, Hero.tsx, SwitchboardPanel.tsx, FlowRail.tsx, StepNav.tsx
  UploadBox.tsx, LoadingAnimation.tsx, JSONForm.tsx
  ProgressBar.tsx, CompanyCard.tsx
  QuoteTable.tsx, ReportCard.tsx, CallTimeline.tsx
lib/
  api.ts      ← all backend calls
  types.ts    ← all shared shapes
```

## Design notes

The visual language is a "dispatch desk / switchboard" — the site is
literally a console for routing and monitoring phone calls, so the UI leans
into ticket cards (cream, torn-edge paper stock), signal lamps for call
status, and monospace for anything numeric or logged. Palette: graphite
housing, amber signal, teal patch-cable, cream ticket. Fonts: Space Grotesk
(display), Inter (body), IBM Plex Mono (data/log).

## Notes for whoever picks this up next

- Polling intervals (1.5–2s) in `processing/page.tsx` and
  `negotiation/page.tsx` are placeholders — tune them once you know real
  extraction/call latency, or replace with sockets.
- `getQuoteReport`'s red-flag detection is currently done client-side in the
  mock (`> 40% below average`); once the backend has a real red-flag/ranking
  engine, just return `warnings: string[]` directly and delete the mock math.
- File upload currently accepts `.pdf,.png,.jpg,.jpeg,.doc,.docx` client-side;
  keep this in sync with whatever the extraction service actually supports.
