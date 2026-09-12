#!/usr/bin/env node
// Regenerates packages/contracts/src/schema.d.ts from the API's exported
// OpenAPI document. Run `uv run python scripts/export_openapi.py` in
// apps/api first (or use `make contracts`, which does both steps).
import { fileURLToPath } from "node:url";
import path from "node:path";
import openapiTS, { astToString } from "openapi-typescript";
import { writeFileSync } from "node:fs";

const here = path.dirname(fileURLToPath(import.meta.url));
const contractsDir = path.resolve(here, "../../../packages/contracts");
const openapiPath = path.join(contractsDir, "openapi.json");
const outputPath = path.join(contractsDir, "src/schema.d.ts");

const ast = await openapiTS(new URL(`file://${openapiPath}`));
writeFileSync(outputPath, astToString(ast));
console.log(`Wrote ${outputPath}`);
