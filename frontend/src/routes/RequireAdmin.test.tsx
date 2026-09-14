import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { RequireAdmin } from "./RequireAdmin";

const mockUseAuth = vi.fn();
vi.mock("@/lib/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<div>dashboard</div>} />
        <Route element={<RequireAdmin />}>
          <Route path="/admin" element={<div>admin panel</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAdmin", () => {
  it("renders the protected route for an admin user", () => {
    mockUseAuth.mockReturnValue({ user: { role: "admin" } });
    renderAt("/admin");
    expect(screen.getByText("admin panel")).toBeInTheDocument();
  });

  it("redirects a non-admin user away", () => {
    mockUseAuth.mockReturnValue({ user: { role: "user" } });
    renderAt("/admin");
    expect(screen.getByText("dashboard")).toBeInTheDocument();
    expect(screen.queryByText("admin panel")).not.toBeInTheDocument();
  });

  it("redirects when there is no user at all", () => {
    mockUseAuth.mockReturnValue({ user: null });
    renderAt("/admin");
    expect(screen.getByText("dashboard")).toBeInTheDocument();
  });
});
