import type { Critique } from "@/lib/agent";
import { CRITIQUE_VIEW_COUNT, CRITIQUE_VIEW_LABELS, runRenderViewUrl } from "@/lib/agent";
import { Eye } from "lucide-react";

export function CritiquePanel({
  critique,
  originalUrl,
  backend,
  renderRunId,
}: {
  critique: Critique | null;
  originalUrl: string | null;
  backend: string;
  renderRunId: string | null;
}) {
  return (
    <div className="p-4">
      <h2 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-slate-300">
        Visual critique
      </h2>

      <figure className="mb-2 overflow-hidden rounded-md border border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
          input
        </div>
        {originalUrl ? (
          <img src={originalUrl} alt="input" className="aspect-video w-full object-contain" />
        ) : (
          <div className="aspect-video w-full" />
        )}
      </figure>

      <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
        mesh renders ({CRITIQUE_VIEW_COUNT} views)
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {renderRunId ? (
          Array.from({ length: CRITIQUE_VIEW_COUNT }, (_, i) => (
            <figure
              key={i}
              className="w-24 shrink-0 overflow-hidden rounded-md border border-slate-800 bg-slate-900/60"
            >
              <div className="truncate border-b border-slate-800 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-slate-500">
                {CRITIQUE_VIEW_LABELS[i]}
              </div>
              <img
                src={runRenderViewUrl(backend, renderRunId, i)}
                alt={CRITIQUE_VIEW_LABELS[i]}
                className="aspect-square w-full object-contain"
              />
            </figure>
          ))
        ) : (
          <div className="flex aspect-square w-24 items-center justify-center rounded-md border border-dashed border-slate-800 text-slate-700">
            <Eye className="h-5 w-5" strokeWidth={1.2} />
          </div>
        )}
      </div>

      {critique && (
        <div className="mt-3 space-y-2">
          <div
            className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider ${
              critique.matches ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
            }`}
          >
            {critique.matches ? "match" : "no match"}
          </div>
          {critique.reasons && critique.reasons !== "stub" && (
            <p className="text-[12px] leading-relaxed text-slate-400">{critique.reasons}</p>
          )}
          {!critique.matches && critique.suggested_fixes && (
            <p className="text-[12px] leading-relaxed text-slate-500">
              <span className="text-slate-400">Fixes: </span>
              {critique.suggested_fixes}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
