import type { Critique } from "@/lib/agent";
import { Eye } from "lucide-react";

export function CritiquePanel({
  critique,
  originalUrl,
  renderUrl,
}: {
  critique: Critique | null;
  originalUrl: string | null;
  renderUrl: string | null;
}) {
  return (
    <div className="p-4">
      <h2 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-slate-300">
        Visual critique
      </h2>

      <div className="grid grid-cols-2 gap-2">
        <figure className="overflow-hidden rounded-md border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
            input
          </div>
          {originalUrl ? (
            <img src={originalUrl} alt="input" className="aspect-square w-full object-contain" />
          ) : (
            <div className="aspect-square w-full" />
          )}
        </figure>
        <figure className="overflow-hidden rounded-md border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
            render
          </div>
          {renderUrl ? (
            <img src={renderUrl} alt="render" className="aspect-square w-full object-contain" />
          ) : (
            <div className="flex aspect-square w-full items-center justify-center text-slate-700">
              <Eye className="h-6 w-6" strokeWidth={1.2} />
            </div>
          )}
        </figure>
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
