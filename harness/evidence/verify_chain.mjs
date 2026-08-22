#!/usr/bin/env node
/**
 * The independent chain re-walk. Stock Node, no dependencies, no Python.
 *
 * **A drill using the Python encoder to check a chain the Python encoder wrote is
 * checking nothing.** This file exists for the same reason `acs1.mjs` does: the claim
 * Alfred sells is that a third party recomputes the digests without running Alfred's
 * code, and a claim that has only ever been checked by its own author is an assertion.
 *
 * Four rules, and the third is the only one that is not self-referential:
 *
 *  1. **Recompute every link** from the stored columns with `acsSha256`. A row whose
 *     content changed but whose hash column came along with it fails here.
 *  2. **Assert the walk is total** — exactly one genesis, exactly one head, every row
 *     visited exactly once, visited count equal to row count. A check that verifies each
 *     link but never checks they form one path passes on a forked log, and a forked audit
 *     log is the failure the architecture exists to prevent.
 *  3. **Compare against the off-machine anchor.** Without it the drill proves the dump is
 *     internally consistent, which a competent attacker would also arrange. The anchored
 *     head must be *reachable from genesis* in the restored chain: a restore that lost the
 *     tail is internally perfect and missing the anchor.
 *  4. **Refuse an empty input.** A walker handed zero rows reports the same thing as a
 *     walker that found nothing wrong.
 *
 * The table-to-separator map below is duplicated from `harness/evidence/store.py`
 * deliberately. `verdict` and `operator_action` carry no `record_type` column — their
 * record type is the table — and taking it from the export would mean recomputing digests
 * from a separator Python chose. Two maps that disagree make every digest mismatch, which
 * is the loud failure and the right one.
 *
 * **stdout is JSONL: one typed event per line, and JSONL is transport, not derivation**
 * (ADR-0014). Typing the verdict changes how it travels, not who computes it — the re-walk
 * stays an implementation that did not write the chain, and no digest is ever read from a
 * message Python sent. `harness/evidence/anchor.py` dispatches on `type` and refuses any
 * line it does not recognize, so a walker and its parser fail loudly when they drift
 * instead of parsing prose with string surgery. The event vocabulary:
 *
 *   {"type":"walk","table":T,"chain_id":C,"rows":N}   what was handed in and walked
 *   {"type":"head","sha":S}                           reachable head, first 16 chars only
 *   {"type":"anchor","state":A}                       absent | equal | reachable-and-extended
 *   {"type":"error","message":M}                      any refusal; exit code is nonzero
 *
 * A successful walk emits `walk`, then `head`, then `anchor`. A refusal emits `error`.
 * The head stays truncated here on purpose: `derive()` in anchor.py requires the caller's
 * full digest to agree with this prefix, and an anchor built from a truncated claim is a
 * weaker claim that nothing would notice.
 *
 *   node harness/evidence/verify_chain.mjs <export.json> [anchor.json]
 */

import { readFileSync } from "node:fs";
import { acsSha256 } from "../acs/acs1.mjs";

const LINK_RECORD_TYPE = "alfred.evidence.chain_link.v1";

const TABLE_RECORD_TYPE = {
  verdict: "alfred.evidence.verdict.v1",
  operator_action: "alfred.evidence.operator_action.v1",
};

class ChainError extends Error {}

/**
 * A `Map`, not an object literal, and this is not a style choice. `acs1.mjs` refuses a
 * plain object outright: JavaScript cannot tell `1` from `1.0`, so the encoder demands a
 * representation that carries the distinction and rejects the one that cannot. Every
 * value here is a string or null, so nothing needs `f64()` or `BigInt` — but the refusal
 * is what makes the second implementation worth having. Writing this walker against a
 * plain object failed immediately and loudly rather than producing a digest that happened
 * to agree with Python today.
 *
 * Insertion order is irrelevant: ACS-1 sorts keys by UTF-8 bytes.
 */
function linkDigest({ chainId, recordType, prevSha256, bodySha256 }) {
  return acsSha256(
    LINK_RECORD_TYPE,
    new Map([
      ["body_sha256", bodySha256],
      ["chain_id", chainId],
      ["prev_sha256", prevSha256],
      ["record_type", recordType],
    ]),
  );
}

export function walk(exported, anchor = null) {
  const { table, chain_id: chainId, rows } = exported;
  if (!table || !chainId || !Array.isArray(rows)) {
    throw new ChainError("export is missing table, chain_id or rows");
  }
  if (rows.length === 0) {
    // Rule 4. An empty walk is not a clean walk.
    throw new ChainError(`chain ${chainId} exported zero rows; nothing was verified`);
  }

  const fixedType = TABLE_RECORD_TYPE[table];
  if (!fixedType && table !== "run_record") {
    throw new ChainError(`unknown chained table ${table}`);
  }

  // Rule 1, and the successor index that rule 2 needs.
  const successorOf = new Map();
  const byDigest = new Map();
  for (const row of rows) {
    const recordType = table === "run_record" ? row.record_type : fixedType;
    if (!recordType) throw new ChainError(`row ${row.id} carries no record_type`);

    const recomputed = linkDigest({
      chainId,
      recordType,
      prevSha256: row.prev_sha256 ?? null,
      bodySha256: row.body_sha256,
    });
    if (recomputed !== row.sha256) {
      throw new ChainError(
        `row ${row.id}: stored ${row.sha256} but recomputes to ${recomputed}`,
      );
    }
    if (byDigest.has(row.sha256)) {
      throw new ChainError(`row ${row.id}: duplicate digest ${row.sha256}`);
    }
    byDigest.set(row.sha256, row);

    const prev = row.prev_sha256 ?? null;
    if (successorOf.has(prev)) {
      throw new ChainError(
        `chain ${chainId} branches at ${prev === null ? "the genesis position" : prev}`,
      );
    }
    successorOf.set(prev, row.sha256);
  }

  // Rule 2.
  const genesis = successorOf.get(null);
  if (genesis === undefined) throw new ChainError(`chain ${chainId} has no genesis row`);

  const reachable = new Set();
  let cursor = genesis;
  let head = genesis;
  while (cursor !== undefined) {
    if (reachable.has(cursor)) throw new ChainError(`chain ${chainId} cycles at ${cursor}`);
    reachable.add(cursor);
    head = cursor;
    cursor = successorOf.get(cursor);
  }
  if (reachable.size !== rows.length) {
    throw new ChainError(
      `chain ${chainId}: walk visited ${reachable.size} of ${rows.length} rows; ` +
        `the links do not form one path`,
    );
  }

  // Rule 3.
  let anchorState = "absent";
  if (anchor) {
    if (anchor.chain_id !== chainId || anchor.table !== table) {
      throw new ChainError(
        `anchor names ${anchor.table}/${anchor.chain_id}, export is ${table}/${chainId}`,
      );
    }
    if (!reachable.has(anchor.head_sha256)) {
      throw new ChainError(
        `anchored head ${anchor.head_sha256} is not reachable in the restored chain; ` +
          `the restore is internally consistent and missing the anchored state`,
      );
    }
    anchorState = anchor.head_sha256 === head ? "equal" : "reachable-and-extended";
  }

  return { table, chainId, length: reachable.size, head, anchorState };
}

function emit(event) {
  process.stdout.write(`${JSON.stringify(event)}\n`);
}

function main(argv) {
  const [exportPath, anchorPath] = argv;
  if (!exportPath) {
    process.stderr.write("usage: verify_chain.mjs <export.json> [anchor.json]\n");
    return 2;
  }
  let exported;
  let anchor = null;
  try {
    exported = JSON.parse(readFileSync(exportPath, "utf8"));
    if (anchorPath) anchor = JSON.parse(readFileSync(anchorPath, "utf8"));
  } catch (error) {
    // Every refusal speaks the protocol, including the ones before any row is read.
    emit({ type: "error", message: `input could not be read: ${error.message}` });
    return 1;
  }
  try {
    const result = walk(exported, anchor);
    emit({ type: "walk", table: result.table, chain_id: result.chainId, rows: result.length });
    emit({ type: "head", sha: result.head.slice(0, 16) });
    emit({ type: "anchor", state: result.anchorState });
    return 0;
  } catch (error) {
    if (error instanceof ChainError) {
      emit({ type: "error", message: error.message });
      process.stderr.write(`CHAIN FAILED ${error.message}\n`);
      return 1;
    }
    throw error;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.exit(main(process.argv.slice(2)));
}
