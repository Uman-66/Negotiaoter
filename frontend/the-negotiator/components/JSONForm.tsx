"use client";

import { useState } from "react";
import type { JobSpec } from "@/lib/types";
import { Plus, X } from "lucide-react";

export default function JSONForm({
  spec,
  onChange,
}: {
  spec: JobSpec;
  onChange: (next: JobSpec) => void;
}) {
  const [furnitureInput, setFurnitureInput] = useState("");

  function set<K extends keyof JobSpec>(key: K, value: JobSpec[K]) {
    onChange({ ...spec, [key]: value });
  }

  function addFurniture() {
    const val = furnitureInput.trim();
    if (!val) return;
    set("furniture", [...spec.furniture, val]);
    setFurnitureInput("");
  }

  function removeFurniture(item: string) {
    set("furniture", spec.furniture.filter((f) => f !== item));
  }

  return (
    <div className="ticket flex flex-col gap-6 rounded-sm p-6 sm:p-8">
      <div className="grid gap-6 sm:grid-cols-2">
        <Field label="Cleaning type">
          <select
            value={spec.cleaningType}
            onChange={(e) => set("cleaningType", e.target.value)}
            className="input"
          >
            <option>Standard Cleaning</option>
            <option>Deep Cleaning</option>
            <option>Move-out Cleaning</option>
            <option>Post-Construction Cleaning</option>
          </select>
        </Field>
        <Field label="House size (sqft)">
          <input
            type="number"
            value={spec.houseSizeSqft}
            onChange={(e) => set("houseSizeSqft", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Bedrooms">
          <input
            type="number"
            min={0}
            value={spec.bedrooms}
            onChange={(e) => set("bedrooms", Number(e.target.value))}
            className="input"
          />
        </Field>
        <Field label="Bathrooms">
          <input
            type="number"
            min={0}
            value={spec.bathrooms}
            onChange={(e) => set("bathrooms", Number(e.target.value))}
            className="input"
          />
        </Field>
      </div>

      <Field label="Furniture">
        <div className="flex flex-wrap gap-2">
          {spec.furniture.map((item) => (
            <span
              key={item}
              className="flex items-center gap-1.5 rounded-full bg-graphite-100 px-3 py-1.5 font-body text-xs text-graphite-800"
            >
              {item}
              <button onClick={() => removeFurniture(item)} aria-label={`Remove ${item}`}>
                <X size={12} className="text-graphite-500 hover:text-signal-red" />
              </button>
            </span>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            value={furnitureInput}
            onChange={(e) => setFurnitureInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addFurniture())}
            placeholder="Add an item, e.g. Bookshelf"
            className="input flex-1"
          />
          <button
            onClick={addFurniture}
            className="flex items-center gap-1 rounded-sm border border-graphite-300 px-3 py-2 font-mono text-xs uppercase tracking-wide text-graphite-700 transition hover:border-teal hover:text-teal-dark"
          >
            <Plus size={14} /> Add
          </button>
        </div>
      </Field>

      <Field label="Special notes">
        <textarea
          value={spec.specialNotes}
          onChange={(e) => set("specialNotes", e.target.value)}
          rows={3}
          className="input resize-none"
        />
      </Field>

      <style jsx global>{`
        .input {
          width: 100%;
          border-radius: 2px;
          border: 1px solid #c3c9d0;
          background: #fff;
          padding: 0.6rem 0.75rem;
          font-family: var(--font-body);
          font-size: 0.875rem;
          color: #20242a;
        }
        .input:focus {
          outline: 2px solid #3e7c7c;
          outline-offset: 1px;
          border-color: #3e7c7c;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="font-mono text-[11px] uppercase tracking-widest text-graphite-500">{label}</span>
      {children}
    </label>
  );
}
