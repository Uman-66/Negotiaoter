"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText, X } from "lucide-react";

interface UploadBoxProps {
  onFileSelected: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
}

export default function UploadBox({ onFileSelected, selectedFile, onClear }: UploadBoxProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onFileSelected(file);
    },
    [onFileSelected]
  );

  if (selectedFile) {
    return (
      <div className="ticket flex items-center justify-between gap-4 rounded-sm p-5">
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-teal-dark" />
          <div>
            <p className="font-body text-sm font-medium text-graphite-800">{selectedFile.name}</p>
            <p className="font-mono text-xs text-graphite-500">
              {(selectedFile.size / 1024).toFixed(0)} KB
            </p>
          </div>
        </div>
        <button
          onClick={onClear}
          aria-label="Remove file"
          className="rounded-full p-1.5 text-graphite-500 transition hover:bg-graphite-100 hover:text-graphite-800"
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-sm border-2 border-dashed px-6 py-16 text-center transition ${
        dragging
          ? "border-amber bg-amber/5"
          : "border-graphite-500/50 hover:border-teal-light hover:bg-graphite-700/40"
      }`}
    >
      <UploadCloud size={30} className={dragging ? "text-amber" : "text-graphite-300"} />
      <div>
        <p className="font-body text-sm font-medium text-ticket">
          Drag &amp; drop your cleaning spec
        </p>
        <p className="mt-1 font-mono text-xs text-graphite-400">PDF, JPG, PNG, or WEBP &middot; up to 20MB</p>
      </div>
      <span className="mt-2 rounded-sm border border-graphite-400/60 px-4 py-2 font-mono text-xs uppercase tracking-widest text-graphite-200 transition hover:border-amber hover:text-amber">
        Choose file
      </span>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.webp"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFileSelected(file);
        }}
      />
    </div>
  );
}
