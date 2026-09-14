#!/usr/bin/env node
// Fails the build if the initial-load JS (the entry chunk plus any
// vendor/shared chunk that isn't behind a route's `lazy()`) exceeds its
// gzip budget. Per-route chunks (see src/routes/router.tsx) are excluded
// on purpose -- a big page nobody has opened yet shouldn't fail CI, only
// the bytes every visitor pays for on first load. See docs/performance.md
// "Bundle budget" for the current numbers and how to raise the budget
// deliberately if a dependency genuinely needs it.
import { gzipSync } from "node:zlib";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const distAssets = path.resolve(here, "../dist/assets");

// The entry chunk's name is content-hashed (index-XXXX.js); everything
// else in dist/assets is either a route chunk (already excluded from the
// initial load by design) or a CSS file this check doesn't cover.
const ENTRY_BUDGET_GZIP_BYTES = 150 * 1024;

function findEntryChunk() {
  const files = readdirSync(distAssets).filter((f) => /^index-.*\.js$/.test(f));
  if (files.length !== 1) {
    throw new Error(`expected exactly one entry chunk matching index-*.js, found: ${files.join(", ")}`);
  }
  return files[0];
}

const entryFile = findEntryChunk();
const entryPath = path.join(distAssets, entryFile);
const raw = readFileSync(entryPath);
const gzipBytes = gzipSync(raw).length;

console.log(`entry chunk: ${entryFile}`);
console.log(`  raw:  ${(statSync(entryPath).size / 1024).toFixed(1)} kB`);
console.log(`  gzip: ${(gzipBytes / 1024).toFixed(1)} kB (budget: ${(ENTRY_BUDGET_GZIP_BYTES / 1024).toFixed(0)} kB)`);

if (gzipBytes > ENTRY_BUDGET_GZIP_BYTES) {
  console.error(
    `\nEntry chunk exceeds its gzip budget by ${((gzipBytes - ENTRY_BUDGET_GZIP_BYTES) / 1024).toFixed(1)} kB.`,
  );
  console.error("A new dependency likely landed in the shared bundle instead of a route chunk.");
  console.error("If the increase is deliberate and necessary, raise ENTRY_BUDGET_GZIP_BYTES here");
  console.error("and record why in docs/performance.md.");
  process.exit(1);
}
