/**
 * Workspace Hub: every asset saved across every hub, in one searchable
 * place. Left rail of typed collections (FRD §19) plus user folders
 * with drag-and-drop; a grid/list main area with per-type preview
 * cards, backed by VirtualRows so the DOM stays bounded regardless of
 * how many assets a user has saved; instant debounced search with
 * highlighted matches; sticky bulk-action bar; a detail drawer that
 * shows the tool run behind an asset and lets you re-run it; export;
 * and a 30-day trash with restore.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type {
  AssetFolderResponse,
  AssetListResponse,
  AssetVersionResponse,
  ToolRunSummary,
  WorkspaceAssetResponse,
} from "@linksavvy/contracts";
import { apiFetch, getAccessToken } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { VirtualRows } from "@/workspace/VirtualRows";

type AssetType = WorkspaceAssetResponse["type"];

interface Collection {
  key: string;
  label: string;
  type?: AssetType;
  favouritesOnly?: boolean;
}

const COLLECTIONS: Collection[] = [
  { key: "all", label: "All" },
  { key: "post", label: "Saved Posts", type: "post" },
  { key: "template", label: "Templates", type: "template" },
  { key: "resume", label: "Résumés", type: "resume" },
  { key: "job_description", label: "Job Descriptions", type: "job_description" },
  { key: "conversation", label: "Conversations", type: "conversation" },
  { key: "analysis", label: "Analyses", type: "analysis" },
  { key: "favourites", label: "Favourites", favouritesOnly: true },
];

type Selection =
  { kind: "collection"; key: string } | { kind: "folder"; id: string } | { kind: "trash" };

const GRID_COLUMNS = 3;
const ROW_HEIGHT_GRID = 180;
const ROW_HEIGHT_LIST = 84;
const VIEWPORT_HEIGHT = 560;
const SEARCH_DEBOUNCE_MS = 300;

function highlight(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;
  const index = text.toLowerCase().indexOf(query.toLowerCase());
  if (index === -1) return text;
  return (
    <>
      {text.slice(0, index)}
      <mark className="bg-warning/40 text-fg">{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  );
}

function previewText(asset: WorkspaceAssetResponse): string {
  const opening = asset.body.split("\n").find((line) => line.trim().length > 0) ?? asset.body;
  return opening.length > 160 ? `${opening.slice(0, 160)}…` : opening;
}

function AssetCard({
  asset,
  query,
  selected,
  focused,
  onToggleSelect,
  onOpen,
  onDragStart,
  view,
}: {
  asset: WorkspaceAssetResponse;
  query: string;
  selected: boolean;
  focused: boolean;
  onToggleSelect: () => void;
  onOpen: () => void;
  onDragStart: (e: React.DragEvent) => void;
  view: "grid" | "list";
}) {
  const scoreFromMetadata =
    asset.type === "analysis" && typeof asset.metadata.score === "number"
      ? (asset.metadata.score as number)
      : null;

  return (
    <div
      draggable
      onDragStart={onDragStart}
      data-testid="asset-card"
      data-asset-id={asset.id}
      className={`flex cursor-pointer flex-col gap-2 rounded-lg border p-3 transition-colors ${
        focused ? "border-primary" : "border-border"
      } ${view === "list" ? "flex-row items-center" : ""}`}
      onClick={onOpen}
    >
      <div className="flex items-start justify-between gap-2">
        <input
          type="checkbox"
          checked={selected}
          onClick={(e) => e.stopPropagation()}
          onChange={onToggleSelect}
          aria-label={`Select ${asset.title}`}
        />
        <span className="flex-1 text-sm font-medium text-fg">{highlight(asset.title, query)}</span>
        {asset.is_favourite && <Badge variant="warning">★</Badge>}
      </div>
      {asset.type === "resume" ? (
        <div className="flex h-16 items-center justify-center rounded bg-bg-subtle text-fg-muted">
          📄 Résumé
        </div>
      ) : scoreFromMetadata !== null ? (
        <p className="text-2xl font-semibold text-fg">{scoreFromMetadata}/100</p>
      ) : (
        <p className="text-xs text-fg-muted">{highlight(previewText(asset), query)}</p>
      )}
      <div className="flex flex-wrap gap-1">
        {asset.tags.map((tag) => (
          <Badge key={tag}>{tag}</Badge>
        ))}
      </div>
    </div>
  );
}

function DetailDrawer({
  asset,
  onClose,
  onExport,
  onDuplicate,
}: {
  asset: WorkspaceAssetResponse;
  onClose: () => void;
  onExport: (format: "txt" | "md" | "pdf" | "docx") => void;
  onDuplicate: () => void;
}) {
  const [versions, setVersions] = useState<AssetVersionResponse[] | null>(null);
  const [run, setRun] = useState<ToolRunSummary | null>(null);

  useEffect(() => {
    setVersions(null);
    setRun(null);
    apiFetch<AssetVersionResponse[]>(`/api/v1/assets/${asset.id}/versions`).then(setVersions);
    if (asset.source_tool_run_id) {
      apiFetch<ToolRunSummary>(`/api/v1/tools/runs/${asset.source_tool_run_id}`)
        .then(setRun)
        .catch(() => setRun(null));
    }
  }, [asset.id, asset.source_tool_run_id]);

  return (
    <Modal open onClose={onClose} title={asset.title} className="max-w-lg">
      <div className="flex flex-col gap-4">
        <div className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-md border border-border p-3 text-sm text-fg">
          {asset.body}
        </div>

        <dl className="grid grid-cols-2 gap-2 text-xs text-fg-muted">
          <dt>Type</dt>
          <dd>{asset.type}</dd>
          <dt>Created</dt>
          <dd>{new Date(asset.created_at).toLocaleString()}</dd>
          <dt>Updated</dt>
          <dd>{new Date(asset.updated_at).toLocaleString()}</dd>
        </dl>

        {run && (
          <div className="rounded-md border border-border p-3">
            <p className="text-xs font-medium text-fg-muted">Produced by</p>
            <p className="text-sm text-fg">{run.tool_id}</p>
            <Link to={`/${run.tool_id.split(".")[0]}/${run.tool_id}?run_id=${run.id}`}>
              <Button size="sm" variant="secondary" className="mt-2">
                Open in tool
              </Button>
            </Link>
          </div>
        )}

        {versions && versions.length > 0 && (
          <div>
            <p className="mb-1 text-xs font-medium text-fg-muted">Version history</p>
            <ul className="flex flex-col gap-1 text-xs text-fg-muted">
              {versions.map((v) => (
                <li key={v.version}>
                  v{v.version} — {v.title} ({new Date(v.created_at).toLocaleDateString()})
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={onDuplicate}>
            Duplicate
          </Button>
          {(["txt", "md", "pdf", "docx"] as const).map((format) => (
            <Button key={format} size="sm" variant="ghost" onClick={() => onExport(format)}>
              Export {format.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>
    </Modal>
  );
}

async function downloadBlob(path: string, filename: string) {
  const token = getAccessToken();
  const response = await fetch(path, {
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) throw new Error("Export failed");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function WorkspaceHubPage() {
  const { push } = useToast();
  const [selection, setSelection] = useState<Selection>({ kind: "collection", key: "all" });
  const [view, setView] = useState<"grid" | "list">("grid");
  const [rawQuery, setRawQuery] = useState("");
  const [query, setQuery] = useState("");
  const [assets, setAssets] = useState<WorkspaceAssetResponse[] | null>(null);
  const [trash, setTrash] = useState<WorkspaceAssetResponse[] | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [folders, setFolders] = useState<AssetFolderResponse[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailAsset, setDetailAsset] = useState<WorkspaceAssetResponse | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [undoAsset, setUndoAsset] = useState<WorkspaceAssetResponse | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setQuery(rawQuery), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [rawQuery]);

  const loadFolders = useCallback(() => {
    apiFetch<AssetFolderResponse[]>("/api/v1/asset-folders").then(setFolders);
  }, []);

  useEffect(() => {
    loadFolders();
  }, [loadFolders]);

  const loadAssets = useCallback(
    (cursor?: string) => {
      if (selection.kind === "trash") {
        apiFetch<WorkspaceAssetResponse[]>("/api/v1/assets/trash").then(setTrash);
        return;
      }
      const params = new URLSearchParams();
      if (selection.kind === "collection") {
        const collection = COLLECTIONS.find((c) => c.key === selection.key);
        if (collection?.type) params.set("type", collection.type);
        if (collection?.favouritesOnly) params.set("favourite", "true");
      } else if (selection.kind === "folder") {
        params.set("folder_id", selection.id);
      }
      if (query) params.set("q", query);
      if (cursor) params.set("cursor", cursor);
      apiFetch<AssetListResponse>(`/api/v1/assets?${params.toString()}`).then((page) => {
        setAssets((current) => (cursor ? [...(current ?? []), ...page.items] : page.items));
        setNextCursor(page.next_cursor);
      });
    },
    [selection, query],
  );

  useEffect(() => {
    setAssets(null);
    setSelectedIds(new Set());
    setFocusedIndex(0);
    loadAssets();
  }, [loadAssets]);

  const toggleSelect = (id: string) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const currentList = selection.kind === "trash" ? trash : assets;

  const focusedAsset = currentList?.[focusedIndex] ?? null;

  const toggleFavourite = (asset: WorkspaceAssetResponse) => {
    apiFetch<WorkspaceAssetResponse>(`/api/v1/assets/${asset.id}`, {
      method: "PATCH",
      body: { is_favourite: !asset.is_favourite },
    }).then((updated) => {
      setAssets((current) => current?.map((a) => (a.id === updated.id ? updated : a)) ?? current);
    });
  };

  const trashAsset = useCallback((asset: WorkspaceAssetResponse) => {
    apiFetch(`/api/v1/assets/${asset.id}`, { method: "DELETE" }).then(() => {
      setAssets((current) => current?.filter((a) => a.id !== asset.id) ?? current);
      setUndoAsset(asset);
    });
  }, []);

  const undoTrash = () => {
    if (!undoAsset) return;
    apiFetch<WorkspaceAssetResponse>(`/api/v1/assets/${undoAsset.id}/restore`, {
      method: "POST",
    }).then(() => {
      setUndoAsset(null);
      loadAssets();
    });
  };

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const active = document.activeElement;
      const isTyping = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement;

      if (e.key === "/" && !isTyping) {
        e.preventDefault();
        searchInputRef.current?.focus();
        return;
      }
      if (isTyping) return;

      if (!currentList || currentList.length === 0) return;
      const columns = view === "grid" ? GRID_COLUMNS : 1;

      if (e.key === "ArrowRight") setFocusedIndex((i) => Math.min(currentList.length - 1, i + 1));
      else if (e.key === "ArrowLeft") setFocusedIndex((i) => Math.max(0, i - 1));
      else if (e.key === "ArrowDown")
        setFocusedIndex((i) => Math.min(currentList.length - 1, i + columns));
      else if (e.key === "ArrowUp") setFocusedIndex((i) => Math.max(0, i - columns));
      else if (e.key === "f" && focusedAsset) toggleFavourite(focusedAsset);
      else if (e.key === "Delete" && focusedAsset && selection.kind !== "trash")
        trashAsset(focusedAsset);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [currentList, view, focusedAsset, selection.kind, trashAsset]);

  const handleDropOnFolder = (folderId: string | null, assetId: string) => {
    apiFetch(`/api/v1/assets/${assetId}`, {
      method: "PATCH",
      body: folderId ? { folder_id: folderId } : { unfile: true },
    }).then(() => loadAssets());
  };

  const runBulk = (
    action: "move" | "tag" | "delete" | "export",
    extra: Record<string, unknown> = {},
  ) => {
    apiFetch(`/api/v1/assets/bulk`, {
      method: "POST",
      body: { action, asset_ids: Array.from(selectedIds), ...extra },
    }).then(() => {
      setSelectedIds(new Set());
      loadAssets();
      push({
        title: `${action.charAt(0).toUpperCase()}${action.slice(1)} applied.`,
        variant: "success",
      });
    });
  };

  const exportSelection = async () => {
    const token = getAccessToken();
    const response = await fetch("/api/v1/assets/bulk", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        action: "export",
        asset_ids: Array.from(selectedIds),
        format: "txt",
      }),
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "workspace-export.zip";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-full gap-6">
      <aside className="w-56 shrink-0 border-r border-border pr-4">
        <h1 className="mb-4 text-xl font-semibold text-fg">Workspace</h1>
        <nav className="flex flex-col gap-1">
          {COLLECTIONS.map((collection) => (
            <button
              key={collection.key}
              className={`rounded-md px-2 py-1.5 text-left text-sm ${
                selection.kind === "collection" && selection.key === collection.key
                  ? "bg-primary/10 text-primary"
                  : "text-fg hover:bg-bg-subtle"
              }`}
              onClick={() => setSelection({ kind: "collection", key: collection.key })}
            >
              {collection.label}
            </button>
          ))}
        </nav>
        <p className="mb-1 mt-4 text-xs font-medium uppercase tracking-wide text-fg-muted">
          Folders
        </p>
        <nav className="flex flex-col gap-1">
          {folders.map((folder) => (
            <button
              key={folder.id}
              className={`rounded-md px-2 py-1.5 text-left text-sm ${
                selection.kind === "folder" && selection.id === folder.id
                  ? "bg-primary/10 text-primary"
                  : "text-fg hover:bg-bg-subtle"
              }`}
              onClick={() => setSelection({ kind: "folder", id: folder.id })}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                const assetId = e.dataTransfer.getData("text/asset-id");
                if (assetId) handleDropOnFolder(folder.id, assetId);
              }}
            >
              📁 {folder.name}
            </button>
          ))}
        </nav>
        <button
          className={`mt-4 rounded-md px-2 py-1.5 text-left text-sm ${
            selection.kind === "trash" ? "bg-primary/10 text-primary" : "text-fg hover:bg-bg-subtle"
          }`}
          onClick={() => setSelection({ kind: "trash" })}
        >
          🗑 Trash
        </button>
      </aside>

      <div className="flex flex-1 flex-col gap-4">
        <div className="flex items-center gap-3">
          <input
            ref={searchInputRef}
            type="text"
            value={rawQuery}
            onChange={(e) => setRawQuery(e.target.value)}
            placeholder="Search your workspace... (press / to focus)"
            className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-fg"
          />
          <Button
            size="sm"
            variant={view === "grid" ? "primary" : "secondary"}
            onClick={() => setView("grid")}
          >
            Grid
          </Button>
          <Button
            size="sm"
            variant={view === "list" ? "primary" : "secondary"}
            onClick={() => setView("list")}
          >
            List
          </Button>
        </div>

        {undoAsset && (
          <div className="flex items-center justify-between rounded-md border border-border bg-bg-subtle px-3 py-2 text-sm">
            <span>"{undoAsset.title}" moved to trash.</span>
            <Button size="sm" variant="ghost" onClick={undoTrash}>
              Undo
            </Button>
          </div>
        )}

        {selectedIds.size > 0 && (
          <div className="sticky top-0 z-10 flex items-center gap-2 rounded-md border border-border bg-card p-3 shadow-sm">
            <span className="text-sm text-fg">{selectedIds.size} selected</span>
            <Button size="sm" variant="secondary" onClick={() => runBulk("delete")}>
              Delete
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => runBulk("tag", { tags: ["reviewed"] })}
            >
              Tag as reviewed
            </Button>
            <Button size="sm" variant="secondary" onClick={exportSelection}>
              Export ZIP
            </Button>
          </div>
        )}

        {selection.kind === "trash" ? (
          trash === null ? (
            <Skeleton className="h-40 w-full" />
          ) : trash.length === 0 ? (
            <EmptyState
              title="Trash is empty"
              description="Deleted assets appear here for 30 days."
            />
          ) : (
            <ul className="flex flex-col gap-2">
              {trash.map((asset) => (
                <li
                  key={asset.id}
                  className="flex items-center justify-between rounded-md border border-border p-3"
                >
                  <span className="text-sm text-fg">{asset.title}</span>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() =>
                        apiFetch(`/api/v1/assets/${asset.id}/restore`, { method: "POST" }).then(
                          () => loadAssets(),
                        )
                      }
                    >
                      Restore
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() =>
                        apiFetch(`/api/v1/assets/${asset.id}?permanent=true`, {
                          method: "DELETE",
                        }).then(() => loadAssets())
                      }
                    >
                      Delete forever
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )
        ) : assets === null ? (
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-40 w-full" />
            ))}
          </div>
        ) : assets.length === 0 ? (
          <EmptyState
            title="Nothing here yet"
            description="Generate something in a hub and save it to see it appear here."
          />
        ) : (
          <>
            <VirtualRows
              items={assets}
              columns={view === "grid" ? GRID_COLUMNS : 1}
              rowHeight={view === "grid" ? ROW_HEIGHT_GRID : ROW_HEIGHT_LIST}
              height={VIEWPORT_HEIGHT}
              renderItem={(asset, index) => (
                <AssetCard
                  asset={asset}
                  query={query}
                  view={view}
                  selected={selectedIds.has(asset.id)}
                  focused={index === focusedIndex}
                  onToggleSelect={() => toggleSelect(asset.id)}
                  onOpen={() => {
                    setFocusedIndex(index);
                    setDetailAsset(asset);
                  }}
                  onDragStart={(e: React.DragEvent) =>
                    e.dataTransfer.setData("text/asset-id", asset.id)
                  }
                />
              )}
              getKey={(asset) => asset.id}
            />
            {nextCursor && (
              <Button variant="secondary" onClick={() => loadAssets(nextCursor)}>
                Load more
              </Button>
            )}
          </>
        )}
      </div>

      {detailAsset && (
        <DetailDrawer
          asset={detailAsset}
          onClose={() => setDetailAsset(null)}
          onExport={(format) =>
            downloadBlob(
              `/api/v1/assets/${detailAsset.id}/export?format=${format}`,
              `${detailAsset.title}.${format}`,
            )
          }
          onDuplicate={() =>
            apiFetch(`/api/v1/assets/${detailAsset.id}/duplicate`, { method: "POST" }).then(() => {
              setDetailAsset(null);
              loadAssets();
            })
          }
        />
      )}
    </div>
  );
}
