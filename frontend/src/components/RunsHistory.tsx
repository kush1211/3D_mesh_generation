import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, XCircle, RefreshCw, Box } from "lucide-react";
import type { RunMeta } from "@/lib/agent";
import { listRuns, fetchGlbObjectUrl } from "@/lib/agent";

export function RunsHistory({
  backend,
  onLoad,
  refreshTrigger,
}: {
  backend: string;
  onLoad: (glbUrl: string, run: RunMeta) => void;
  refreshTrigger: number;
}) {
  const [runs, setRuns] = useState<RunMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const fetchRuns = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listRuns(backend);
      setRuns(data);
    } catch {
      // backend offline — silently keep empty list
    } finally {
      setLoading(false);
    }
  }, [backend]);

  useEffect(() => { fetchRuns(); }, [fetchRuns, refreshTrigger]);

  const handleLoad = async (run: RunMeta) => {
    if (!run.has_glb) return;
    setLoadingId(run.run_id);
    try {
      const url = await fetchGlbObjectUrl(backend, run.run_id);
      onLoad(url, run);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="flex flex-col gap-1 p-3">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-widest text-slate-400">
          History
        </span>
        <button
          onClick={fetchRuns}
          className="rounded p-1 text-slate-500 hover:text-slate-300"
          title="Refresh"
        >
          <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {runs.length === 0 && !loading && (
        <p className="py-4 text-center font-mono text-[10px] text-slate-600">no runs yet</p>
      )}

      {runs.map((run) => (
        <button
          key={run.run_id}
          onClick={() => handleLoad(run)}
          disabled={!run.has_glb || loadingId === run.run_id}
          className="group flex w-full items-start gap-2 rounded-md border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-left transition hover:border-slate-600 hover:bg-slate-800/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {/* render thumbnail */}
          <div className="mt-0.5 h-10 w-10 shrink-0 overflow-hidden rounded border border-slate-700 bg-slate-800">
            {run.has_render ? (
              <img
                src={`${backend}/runs/${run.run_id}/render.png`}
                alt="render"
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-slate-600">
                <Box className="h-4 w-4" strokeWidth={1.2} />
              </div>
            )}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              {run.status === "success" ? (
                <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-400" />
              ) : (
                <XCircle className="h-3 w-3 shrink-0 text-rose-400" />
              )}
              <span className="truncate font-mono text-[11px] text-slate-300">
                {run.filename}
              </span>
            </div>
            <div className="mt-0.5 font-mono text-[10px] text-slate-600">
              {new Date(run.ts * 1000).toLocaleString()} · iter {run.iteration ?? "—"}
            </div>
          </div>

          {loadingId === run.run_id && (
            <RefreshCw className="mt-1 h-3 w-3 shrink-0 animate-spin text-emerald-400" />
          )}
        </button>
      ))}
    </div>
  );
}
