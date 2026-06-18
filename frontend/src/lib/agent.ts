// Talks to the FastAPI backend: streams the agent loop and fetches artifacts.

export type Dimensions = { width_m: number; height_m: number; depth_m: number };

export type Plan = {
  object_type: string;
  description: string;
  operations: string[];
  expected_topology: string;
  expected_euler: number;
  dimensions: Dimensions;
  notes: string;
};

export type Validation = {
  is_watertight: boolean;
  is_winding_consistent: boolean;
  euler_number: number;
  expected_euler: number | null;
  bounds: number[][];
  extents: number[];
  volume: number;
  dims_ok: boolean;
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
  | { type: "start"; max_iterations: number; stub: boolean }
  | {
      type: "node";
      node: string;
      iteration?: number;
      plan?: Plan;
      validation?: Validation;
      critique?: Critique;
      execution?: Execution;
      code_len?: number;
      feedback?: string;
      status?: string;
    }
  | {
      type: "done";
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

export async function getHealth(backend: string): Promise<Health> {
  const res = await fetch(`${backend}/health`);
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

// Stream NDJSON events from POST /run, calling onEvent per line.
export async function runAgent(
  backend: string,
  file: File,
  stub: boolean,
  onEvent: (e: AgentEvent) => void,
): Promise<void> {
  const fd = new FormData();
  fd.append("image", file);
  fd.append("stub", String(stub));

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
export async function fetchGlbObjectUrl(backend: string): Promise<string> {
  const res = await fetch(`${backend}/mesh.glb?t=${Date.now()}`);
  if (!res.ok) throw new Error("no glb");
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
