import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { NotificationBell } from "./NotificationBell";

vi.mock("@/lib/notifications-api", () => ({
  listNotifications: vi.fn(),
  markNotificationRead: vi.fn().mockResolvedValue(undefined),
  markAllNotificationsRead: vi.fn().mockResolvedValue(undefined),
}));

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/notifications-api";

const mockedList = vi.mocked(listNotifications);

function page(unreadCount: number) {
  return {
    unread_count: unreadCount,
    items: [
      {
        id: "n1",
        type: "audit.completed",
        title: "Your audit is ready",
        body: "Score: 82",
        action_route: "/dashboard",
        metadata: {},
        read_at: null,
        created_at: new Date().toISOString(),
      },
    ],
  };
}

describe("NotificationBell", () => {
  it("shows the unread count badge and lists notifications", async () => {
    mockedList.mockResolvedValue(page(1));
    render(
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("1")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /notifications/i }));
    expect(await screen.findByText("Your audit is ready")).toBeInTheDocument();
  });

  it("marks a notification read when clicked", async () => {
    mockedList.mockResolvedValue(page(1));
    render(
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /notifications/i }));

    fireEvent.click(await screen.findByText("Your audit is ready"));
    await waitFor(() => expect(markNotificationRead).toHaveBeenCalledWith("n1"));
  });

  it("marks all as read", async () => {
    mockedList.mockResolvedValue(page(1));
    render(
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("1")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /notifications/i }));

    fireEvent.click(await screen.findByText("Mark all read"));
    await waitFor(() => expect(markAllNotificationsRead).toHaveBeenCalled());
  });
});
