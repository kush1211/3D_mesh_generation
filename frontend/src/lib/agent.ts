// Talks to the FastAPI backend: streams the agent loop and fetches artifacts.

export type Validation = {
  is_watertight: boolean;
  is_winding_consistent: boolean;
  euler_number: number;
  expected_euler: number | null;
  bounds: number[][];
  extents: number[];
  volume: number;
  dims_ok: boolean | null;
  passed: boolean;
};

export type Critique = {
  matches: boolean;
  reasons: string;
  suggested_fixes: string;
};

export type Execution = {
  ok: boolean;
  returncode: number;
  timed_out: boolean;
  stderr_tail: string;
};

export type AgentEvent =
  | { type: "start"; max_iterations: number }
  | {
      type: "node";
      node: string;
      iteration?: number;
      validation?: Validation;
      critique?: Critique;
      execution?: Execution;
      code_len?: number;
      feedback?: string;
      status?: string;
    }
  | {
      type: "done";
      run_id: string;
      status: string;
      iteration?: number;
      validation?: Validation | null;
      critique?: Critique | null;
      has_glb: boolean;
      has_render: boolean;
      ts: number;
    }
  | { type: "error"; message: string };

export type Health = { ok: boolean; has_key: boolean; model: string };

export type RunMeta = {
  run_id: string;
  filename: string;
  ts: number;
  status: string;
  iteration: number | null;
  validation: Validation | null;
  critique: Critique | null;
  has_glb: boolean;
  has_render: boolean;
};

export async function getHealth(backend: string): Promise<Health> {
  const res = await fetch(`${backend}/health`);
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

// Stream NDJSON events from POST /run, calling onEvent per line.
export async function runAgent(
  backend: string,
  file: File,
  onEvent: (e: AgentEvent) => void,
): Promise<void> {
  const fd = new FormData();
  fd.append("image", file);

  const res = await fetch(`${backend}/run`, { method: "POST", body: fd });
  if (!res.ok || !res.body) throw new Error(`Backend error ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  const flush = (line: string) => {
    const t = line.trim();
    if (!t) return;
    try {
      onEvent(JSON.parse(t) as AgentEvent);
    } catch {
      /* ignore partial/garbage lines */
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let nl: number;
    while ((nl = buf.indexOf("\n")) >= 0) {
      flush(buf.slice(0, nl));
      buf = buf.slice(nl + 1);
    }
  }
  flush(buf);
}

// Fetch the exported mesh as a same-origin blob URL (avoids cross-origin
// loader quirks when the artifact is opened from file://).
export async function fetchGlbObjectUrl(backend: string, runId?: string): Promise<string> {
  const url = runId ? `${backend}/runs/${runId}/mesh.glb` : `${backend}/mesh.glb?t=${Date.now()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("no glb");
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

export async function listRuns(backend: string): Promise<RunMeta[]> {
  const res = await fetch(`${backend}/runs`);
  if (!res.ok) throw new Error(`runs ${res.status}`);
  return res.json();
}
