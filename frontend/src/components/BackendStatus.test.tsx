import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import BackendStatus from "./BackendStatus";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("BackendStatus", () => {
  it("shows API and database status from /health", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", database: "ok" }), { status: 200 }),
      ),
    );

    render(<BackendStatus />);

    expect(await screen.findByText("API:", { exact: false })).toHaveTextContent("API: ok");
    expect(screen.getByText("Database:", { exact: false })).toHaveTextContent("Database: ok");
  });

  it("shows an error when the backend cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    render(<BackendStatus />);

    expect(await screen.findByText(/Backend unreachable: network down/)).toBeInTheDocument();
  });
});
