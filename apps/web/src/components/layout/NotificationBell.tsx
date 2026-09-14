/**
 * The in-app notification centre: unread count in the top bar, a
 * dropdown listing recent notifications grouped by read/unread, and
 * mark-one / mark-all-read. Polls rather than streaming -- notifications
 * are inherently bursty and low-frequency, so a 30s poll is plenty
 * fresh without adding a websocket just for this.
 */

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { NotificationResponse } from "@linksavvy/contracts";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/notifications-api";
import { cn } from "@/lib/cn";

const POLL_INTERVAL_MS = 30_000;

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function NotificationBell() {
  const [items, setItems] = useState<NotificationResponse[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  async function refresh() {
    const page = await listNotifications();
    setItems(page.items);
    setUnreadCount(page.unread_count);
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleSelect(notification: NotificationResponse) {
    if (!notification.read_at) {
      await markNotificationRead(notification.id);
      await refresh();
    }
    setOpen(false);
    if (notification.action_route) navigate(notification.action_route);
  }

  async function handleMarkAllRead() {
    await markAllNotificationsRead();
    await refresh();
  }

  const unread = items.filter((n) => !n.read_at);
  const read = items.filter((n) => n.read_at);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        className="relative rounded-md p-2 text-fg hover:bg-bg-subtle"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold text-danger-foreground">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-40 mt-2 w-80 rounded-lg border border-border bg-card shadow-lg">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-sm font-medium text-fg">Notifications</span>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs text-primary hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {items.length === 0 && (
              <p className="p-4 text-sm text-fg-muted">Nothing here yet.</p>
            )}
            {unread.length > 0 && (
              <ul>
                {unread.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onSelect={handleSelect}
                  />
                ))}
              </ul>
            )}
            {read.length > 0 && (
              <ul className="border-t border-border">
                {read.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onSelect={handleSelect}
                  />
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function NotificationItem({
  notification,
  onSelect,
}: {
  notification: NotificationResponse;
  onSelect: (n: NotificationResponse) => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(notification)}
        className={cn(
          "w-full px-3 py-2 text-left hover:bg-bg-subtle",
          !notification.read_at && "bg-primary/5",
        )}
      >
        <p className="text-sm font-medium text-fg">{notification.title}</p>
        <p className="mt-0.5 line-clamp-2 text-xs text-fg-muted">{notification.body}</p>
        <p className="mt-1 text-[11px] text-fg-muted">{timeAgo(notification.created_at)}</p>
      </button>
    </li>
  );
}
