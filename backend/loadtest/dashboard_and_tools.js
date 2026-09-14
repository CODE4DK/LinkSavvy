// k6 load test for the two latency budgets in the FRD: the dashboard
// aggregate endpoint (p95 < 3s) and an AI tool run (p95 < 10s).
//
// This is meant to run against a real deployed environment (staging,
// never production) with seeded test accounts -- it is not exercised in
// CI or this sandbox, since it needs a live server, a live MySQL with
// realistic data volume, and (for the tool-run scenario) live AI
// provider credentials. See docs/performance.md "Load testing" for how
// and when to run it, and docs/runbook.md for the staging setup.
//
// Usage:
//   k6 run --env BASE_URL=https://staging.linksavvy.example \
//          --env TEST_EMAIL=k6-loadtest@example.com \
//          --env TEST_PASSWORD=... \
//          --env TOOL_ID=profile.headline_optimizer \
//          backend/loadtest/dashboard_and_tools.js
//
// The test account should already have at least one completed audit
// (so the dashboard has real data to aggregate, not the fast empty-state
// path) and be on a plan with quota left for TOOL_ID.

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TEST_EMAIL = __ENV.TEST_EMAIL;
const TEST_PASSWORD = __ENV.TEST_PASSWORD;
const TOOL_ID = __ENV.TOOL_ID || "profile.headline_optimizer";

const dashboardDuration = new Trend("dashboard_duration", true);
const toolRunDuration = new Trend("tool_run_duration", true);

export const options = {
  scenarios: {
    dashboard: {
      executor: "constant-vus",
      vus: 10,
      duration: "2m",
      exec: "dashboard",
    },
    tool_run: {
      executor: "constant-vus",
      vus: 3,
      duration: "2m",
      exec: "toolRun",
    },
  },
  thresholds: {
    // FRD targets: dashboard p95 < 3s, AI tool runs p95 < 10s.
    dashboard_duration: ["p(95)<3000"],
    tool_run_duration: ["p(95)<10000"],
    http_req_failed: ["rate<0.01"],
  },
};

function login() {
  const res = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ email: TEST_EMAIL, password: TEST_PASSWORD }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(res, { "login succeeded": (r) => r.status === 200 });
  return res.json("access_token");
}

export function dashboard() {
  const token = login();
  const res = http.get(`${BASE_URL}/api/v1/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  dashboardDuration.add(res.timings.duration);
  check(res, { "dashboard 200": (r) => r.status === 200 });
  sleep(1);
}

export function toolRun() {
  const token = login();
  const res = http.post(
    `${BASE_URL}/api/v1/tools/${TOOL_ID}/run`,
    JSON.stringify({ input: {} }),
    { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } },
  );
  toolRunDuration.add(res.timings.duration);
  check(res, { "tool run 200": (r) => r.status === 200 });
  sleep(2);
}
