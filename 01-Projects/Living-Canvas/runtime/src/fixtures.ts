// Fixture loader (offline, zero network) for T01 replay harness.
// Loads the JSONL event log + seed snapshot into typed in-memory structures.

import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { type SeedSnapshot } from "./state.ts";
import { type Envelope, parseEnvelope } from "./schema.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));

export function fixtureDir(): string {
  return join(__dirname, "..", "..", "fixtures");
}

/** Load and validate seed-concepts.json. */
export function loadSeed(path?: string): SeedSnapshot {
  const p = path ?? join(fixtureDir(), "seed-concepts.json");
  return JSON.parse(readFileSync(p, "utf8")) as SeedSnapshot;
}

/**
 * Load sample-events.jsonl. Blank lines and // comments are skipped; every
 * other line must parse into a valid Envelope (schema errors surface loudly).
 */
export function loadEvents(path?: string): Envelope[] {
  const p = path ?? join(fixtureDir(), "sample-events.jsonl");
  const lines = readFileSync(p, "utf8").split(/\r?\n/);
  const events: Envelope[] = [];
  for (const [i, line] of lines.entries()) {
    const trimmed = line.trim();
    if (trimmed === "" || trimmed.startsWith("//")) continue;
    let raw: unknown;
    try {
      raw = JSON.parse(trimmed);
    } catch (err) {
      throw new Error(`sample-events.jsonl:${i + 1}: failed to parse JSON: ${String(err)}`);
    }
    events.push(parseEnvelope(raw));
  }
  return events;
}