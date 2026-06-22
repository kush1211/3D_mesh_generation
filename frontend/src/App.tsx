import { useCallback, useEffect, useRef, useState } from "react";
import { Boxes, Loader2, Play, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MeshViewer } from "@/components/MeshViewer";
import { LoopTimeline } from "@/components/LoopTimeline";
import { MetricsPanel } from "@/components/MetricsPanel";
import { CritiquePanel } from "@/components/CritiquePanel";
import { UploadPanel } from "@/components/UploadPanel";
import { RunsHistory } from "@/components/RunsHistory";
import {
  runAgent,
  getHealth,
  fetchGlbObjectUrl,
  type AgentEvent,
  type Validation,
  type Critique,
  type Health,
  type RunMeta,
} from "@/lib/agent";

const DEFAULT_BACKEND = "http://127.0.0.1:8000";

export default function App() {
  const [backend, setBackend] = useState(DEFAULT_BACKEND);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthErr, setHealthErr] = useState(false);

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [validation, setValidation] = useState<Validation | null>(null);
  const [critique, setCritique] = useState<Critique | null>(null);
  const [glbUrl, setGlbUrl] = useState<string | null>(null);
  const [renderRunId, setRenderRunId] = useState<string | null>(null);
  const [runToken, setRunToken] = useState(0);

  const glbRef = useRef<string | null>(null);
  const [historyTick, setHistoryTick] = useState(0);

  const checkHealth = useCallback(async () => {
    try {
      const h = await getHealth(backend);
      setHealth(h);
      setHealthErr(false);
    } catch {
      setHealth(null);
      setHealthErr(true);
    }
  }, [backend]);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(f);
    });
  }, []);

  const run = useCallback(async () => {
    if (!file || running) return;
    setRunning(true);
    setEvents([]);
    setValidation(null);
    setCritique(null);
    setRenderRunId(null);
    setRunToken(Date.now());

    try {
      await runAgent(backend, file, (e) => {
        setEvents((prev) => [...prev, e]);
        if (e.type === "node") {
          if (e.validation) setValidation(e.validation);
          if (e.critique) setCritique(e.critique);
        }
        if (e.type === "done") {
          if (e.validation) setValidation(e.validation);
          if (e.critique) setCritique(e.critique);
          if (e.has_render) setRenderRunId(e.run_id);
          if (e.has_glb) {
            fetchGlbObjectUrl(backend, e.run_id)
              .then((url) => {
                if (glbRef.current) URL.revokeObjectURL(glbRef.current);
                glbRef.current = url;
                setGlbUrl(url);
                setHistoryTick((t) => t + 1);
              })
              .catch(() => undefined);
          }
        }
      });
    } catch (err) {
      setEvents((prev) => [...prev, { type: "error", message: String(err) }]);
    } finally {
      setRunning(false);
    }
  }, [backend, file, running]);

  return (
    <div className="flex h-screen flex-col bg-[#0b0e13] text-slate-200">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center gap-4 border-b border-slate-800 px-4">
        <div className="flex items-center gap-2">
          <Boxes className="h-5 w-5 text-emerald-400" />
          <span className="font-semibold tracking-tight">
            mesh<span className="text-emerald-400">forge</span>
          </span>
          <span className="ml-1 hidden font-mono text-[10px] uppercase tracking-widest text-slate-600 sm:inline">
            2D image → validated 3D mesh
          </span>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden items-center gap-2 md:flex">
            <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600">api</span>
            <Input
              value={backend}
              onChange={(e) => setBackend(e.target.value.replace(/\/$/, ""))}
              onBlur={checkHealth}
              spellCheck={false}
              className="h-7 w-52 border-slate-800 bg-slate-900 font-mono text-[11px] text-slate-300"
            />
          </div>

          {healthErr ? (
            <span className="flex items-center gap-1.5 rounded bg-rose-500/10 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-rose-400">
              <WifiOff className="h-3 w-3" /> offline
            </span>
          ) : health ? (
            <span className="flex items-center gap-1.5 rounded bg-emerald-500/10 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-emerald-400">
              <Wifi className="h-3 w-3" /> {health.has_key ? "live" : "no-key"}
            </span>
          ) : null}

          <Button
            onClick={run}
            disabled={!file || running || healthErr}
            className="h-8 gap-1.5 bg-emerald-500 text-slate-950 hover:bg-emerald-400"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {running ? "Running…" : "Generate mesh"}
          </Button>
        </div>
      </header>

      {/* Body */}
      <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[340px_1fr_380px]">
        {/* Left rail */}
        <aside className="flex min-h-0 flex-col overflow-y-auto border-r border-slate-800">
          <UploadPanel
            previewUrl={previewUrl}
            filename={file?.name ?? null}
            disabled={running}
            onFile={handleFile}
          />
          <div className="border-t border-slate-800">
            <RunsHistory
              backend={backend}
              refreshTrigger={historyTick}
              onLoad={(url, run: RunMeta) => {
                if (glbRef.current) URL.revokeObjectURL(glbRef.current);
                glbRef.current = url;
                setGlbUrl(url);
                if (run.validation) setValidation(run.validation);
                if (run.critique) setCritique(run.critique);
                if (run.has_render) setRenderRunId(run.run_id);
              }}
            />
          </div>
        </aside>

        {/* Center viewport */}
        <section className="relative min-h-0">
          <MeshViewer glbUrl={glbUrl} />
        </section>

        {/* Right rail */}
        <aside className="flex min-h-0 flex-col overflow-y-auto border-l border-slate-800">
          <div className="min-h-[220px] flex-1">
            <LoopTimeline
              events={events}
              running={running}
              backend={backend}
              runToken={runToken}
            />
          </div>
          <div className="border-t border-slate-800">
            <MetricsPanel validation={validation} />
            <CritiquePanel
              critique={critique}
              originalUrl={previewUrl}
              backend={backend}
              renderRunId={renderRunId}
            />
          </div>
        </aside>
      </main>
    </div>
  );
}
