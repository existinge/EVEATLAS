// Deterministic canonical serialization.
//
// Two independent replays of the same fixture must yield byte-identical
// canonical JSON + identical commit IDs (GATES.md, Gate P1). Everything that
// participates in the canonical snapshot is derived solely from the seed and
// the appended events, so sorting object keys recursively makes the output
// byte-stable across runs and hosts.

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value !== null && typeof value === "object") {
    const src = value as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const key of Object.keys(src).sort()) {
      const v = src[key];
      if (v !== undefined) out[key] = canonicalize(v);
    }
    return out;
  }
  return value;
}

/** Byte-stable JSON with object keys sorted recursively (no trailing newline). */
export function canonicalJson(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

/** Sorted-key summary used for human-readable reports. */
export function canonicalJsonPretty(value: unknown): string {
  return JSON.stringify(canonicalize(value), null, 2);
}