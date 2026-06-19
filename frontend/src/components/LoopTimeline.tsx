import { useEffect, useRef } from "react";
import {
  Code2,
  Play,
  ShieldCheck,
  Eye,
  Flag,
  CircleDot,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import type { AgentEvent } from "@/lib/agent";

const NODE_META: Record<string, { label: string; Icon: typeof Code2 }> = {
  generate: { label: "Generate code", Icon: Code2 },
  execute: { label: "Execute", Icon: Play },
  validate: { label: "Validate", Icon: ShieldCheck },
  critique: { label: "Render + critique", Icon: Eye },
  finalize: { label: "Finalize", Icon: Flag },
};

type Row = { key: string; label: string; Icon: typeof Code2; detail: string; tone: Tone; iter?: number };
type Tone = "ok" | "fail" | "info" | "warn";

const TONE: Record<Tone, string> = {
  ok: "text-emerald-400",
  fail: "text-rose-400",
  warn: "text-amber-400",
  info: "text-sky-400",
};

function rowFor(e: AgentEvent, i: number): Row | null {
  if (e.type === "start")
    return {
      key: `s${i}`,
      label: "Run started",
      Icon: CircleDot,
      detail: `max ${e.max_iterations} iterations`,
      tone: "info",
    };
  if (e.type === "error")
    return { key: `e${i}`, label: "Error", Icon: AlertTriangle, detail: e.message, tone: "fail" };
  if (e.type === "done")
    return {
      key: `d${i}`,
      label: e.status === "success" ? "Done — success" : "Done — failed",
      Icon: e.status === "success" ? CheckCircle2 : XCircle,
      detail: `${e.iteration ?? "?"} iteration(s)`,
      tone: e.status === "success" ? "ok" : "fail",
    };

  const meta = NODE_META[e.node];
  if (!meta) return null;

  let detail = "";
  let tone: Tone = "info";
  if (e.node === "generate") {
    detail = `${e.code_len ?? 0} chars of trimesh code`;
  } else if (e.node === "execute" && e.execution) {
    tone = e.execution.ok ? "ok" : "fail";
    detail = e.execution.ok ? "script ran, mesh.glb written" : e.execution.stderr_tail || "execution failed";
  } else if (e.node === "validate" && e.validation) {
    tone = e.validation.passed ? "ok" : "fail";
    detail = e.validation.passed
      ? "watertight ✓ winding ✓"
      : "validation failed — see metrics";
  } else if (e.node === "critique" && e.critique) {
    tone = e.critique.matches ? "ok" : "warn";
    detail = e.critique.matches ? "matches the image" : "does not match — retrying";
  } else if (e.node === "finalize") {
    tone = e.status === "success" ? "ok" : "fail";
    detail = `status: ${e.status}`;
  }
  return { key: `n${i}`, label: meta.label, Icon: meta.Icon, detail, tone, iter: e.iteration };
}

export function LoopTimeline({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const rows = events.map(rowFor).filter(Boolean) as Row[];
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [events.length]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2.5">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-widest text-slate-300">
          Agent loop
        </h2>
        {running && <span className="flex h-2 w-2 animate-pulse rounded-full bg-emerald-400" />}
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {rows.length === 0 && (
          <p className="px-2 py-6 text-center font-mono text-xs text-slate-600">
            run the agent to trace generate → execute → validate → critique
          </p>
        )}
        <ol className="relative">
          {rows.map((r, idx) => {
            const Icon = r.Icon;
            return (
              <li key={r.key} className="flex gap-3 px-2 py-1.5">
                <div className="flex flex-col items-center">
                  <Icon className={`h-4 w-4 ${TONE[r.tone]}`} strokeWidth={1.8} />
                  {idx < rows.length - 1 && <span className="mt-1 w-px flex-1 bg-slate-800" />}
                </div>
                <div className="min-w-0 flex-1 pb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200">{r.label}</span>
                    {r.iter != null && (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
                        iter {r.iter}
                      </span>
                    )}
                  </div>
                  {r.detail && (
                    <p
                      className={`font-mono text-[11px] ${r.tone === "fail" ? "whitespace-pre-wrap break-words text-rose-400/80" : "truncate text-slate-500"}`}
                      title={r.detail}
                    >
                      {r.detail}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
        <div ref={endRef} />
      </div>
    </div>
  );
}
