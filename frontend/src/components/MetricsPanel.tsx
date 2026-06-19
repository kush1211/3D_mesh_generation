import type { ReactNode } from "react";
import type { Validation } from "@/lib/agent";
import { Check, X } from "lucide-react";

function Flag({ ok, children }: { ok: boolean; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/60 px-2.5 py-1.5">
      <span className="font-mono text-[11px] text-slate-400">{children}</span>
      {ok ? (
        <Check className="h-3.5 w-3.5 text-emerald-400" strokeWidth={2.5} />
      ) : (
        <X className="h-3.5 w-3.5 text-rose-400" strokeWidth={2.5} />
      )}
    </div>
  );
}

function fmt(n: number, d = 4) {
  return Number.isFinite(n) ? n.toFixed(d) : "—";
}

export function MetricsPanel({ validation }: { validation: Validation | null }) {
  return (
    <div className="border-b border-slate-800 p-4">
      <h2 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-slate-300">
        Validation
      </h2>

      {!validation && (
        <p className="font-mono text-[11px] text-slate-600">no mesh validated yet</p>
      )}

      {validation && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <Flag ok={validation.is_watertight}>watertight</Flag>
            <Flag ok={validation.is_winding_consistent}>winding</Flag>
            <Flag ok={validation.volume > 0}>volume &gt; 0</Flag>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1 font-mono text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-500">euler</span>
              <span className="text-slate-300">{validation.euler_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">volume m³</span>
              <span className="text-slate-300">{fmt(validation.volume, 6)}</span>
            </div>
          </div>

          {validation.extents && (
            <div className="pt-1 font-mono text-[11px]">
              <span className="text-slate-500">extents (m): </span>
              <span className="text-slate-300">
                {validation.extents.map((e) => fmt(e, 3)).join(" × ")}
              </span>
            </div>
          )}

          <div
            className={`mt-2 rounded-md px-2.5 py-1.5 text-center font-mono text-[11px] font-semibold uppercase tracking-wider ${
              validation.passed
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-rose-500/10 text-rose-400"
            }`}
          >
            {validation.passed ? "validation passed" : "validation failed"}
          </div>
        </div>
      )}
    </div>
  );
}
