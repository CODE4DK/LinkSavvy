#!/usr/bin/env node
// Regenerates src/contracts/schema.d.ts from the backend's exported
// OpenAPI document. Run `uv run python scripts/export_openapi.py` in
// backend/ first (or use `make contracts`, which does both steps).
import { fileURLToPath } from "node:url";
import path from "node:path";
import openapiTS, { astToString } from "openapi-typescript";
import { writeFileSync } from "node:fs";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(here, "..");
const openapiPath = path.join(frontendDir, "openapi.json");
const outputPath = path.join(frontendDir, "src/contracts/schema.d.ts");

const ast = await openapiTS(new URL(`file://${openapiPath}`));
writeFileSync(outputPath, astToString(ast));
console.log(`Wrote ${outputPath}`);
