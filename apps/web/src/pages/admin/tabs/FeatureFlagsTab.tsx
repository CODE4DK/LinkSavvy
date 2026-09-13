import { useEffect, useState } from "react";
import type { FeatureFlagResponse } from "@linksavvy/contracts";
import { listFeatureFlags, setFlagGlobal, setFlagRollout, setFlagUserOverride } from "@/lib/admin-api";

export function FeatureFlagsTab() {
  const [flags, setFlags] = useState<FeatureFlagResponse[]>([]);

  async function refresh() {
    setFlags(await listFeatureFlags());
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-border text-left text-fg-muted">
          <th className="py-2 font-normal">Flag</th>
          <th className="py-2 font-normal">Global</th>
          <th className="py-2 font-normal">Rollout %</th>
          <th className="py-2 font-normal">User override</th>
        </tr>
      </thead>
      <tbody>
        {flags.map((flag) => (
          <tr key={flag.key} className="border-b border-border">
            <td className="py-2 text-fg">
              {flag.key}
              {flag.description && <p className="text-xs text-fg-muted">{flag.description}</p>}
            </td>
            <td className="py-2">
              <input
                type="checkbox"
                checked={flag.enabled_globally}
                onChange={async (e) => {
                  await setFlagGlobal(flag.key, { enabled_globally: e.target.checked });
                  await refresh();
                }}
              />
            </td>
            <td className="py-2">
              <input
                type="number"
                min={0}
                max={100}
                defaultValue={flag.rollout_percent}
                className="w-16 rounded-md border border-border bg-bg px-2 py-1 text-fg"
                onBlur={async (e) => {
                  await setFlagRollout(flag.key, { rollout_percent: Number(e.target.value) });
                  await refresh();
                }}
              />
            </td>
            <td className="py-2">
              <button
                type="button"
                onClick={async () => {
                  const userId = window.prompt("User id to override for this flag?");
                  if (!userId) return;
                  const enabledStr = window.prompt("Set to 'true', 'false', or 'clear'?", "true");
                  if (!enabledStr) return;
                  const enabled = enabledStr === "clear" ? null : enabledStr === "true";
                  await setFlagUserOverride(flag.key, { user_id: userId, enabled });
                }}
                className="rounded-md border border-border px-2 py-1 text-xs text-fg"
              >
                Set override
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
