const STEPS = [
  { no: "01", title: "Upload", body: "Drop in a PDF, photo, or doc of your cleaning spec." },
  { no: "02", title: "Extract", body: "We read it into a structured job ticket automatically." },
  { no: "03", title: "Confirm", body: "You review and correct the ticket before anything is sent out." },
  { no: "04", title: "Call", body: "Our agent dials cleaning companies and negotiates live." },
  { no: "05", title: "Compare", body: "Every quote lands in one report, ranked and flagged." },
];

export default function FlowRail() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-16">
      <h2 className="mb-10 font-display text-sm font-bold uppercase tracking-widest text-graphite-300">
        How a job moves through the desk
      </h2>
      <div className="grid gap-px overflow-hidden rounded-sm bg-graphite-500/30 sm:grid-cols-5">
        {STEPS.map((step) => (
          <div key={step.no} className="flex flex-col gap-3 bg-graphite-800 p-5">
            <span className="font-mono text-xs text-amber">{step.no}</span>
            <span className="font-display text-base font-bold text-ticket">{step.title}</span>
            <p className="font-body text-sm leading-snug text-graphite-300">{step.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
