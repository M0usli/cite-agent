"use client";

import { useEffect, useState } from "react";
import { getHealth, type Health } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error"; message: string };

export default function BackendStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    getHealth()
      .then((health) => setState({ kind: "ok", health }))
      .catch((err: unknown) =>
        setState({ kind: "error", message: err instanceof Error ? err.message : String(err) }),
      );
  }, []);

  if (state.kind === "loading") {
    return <p className="text-zinc-500">Checking backend…</p>;
  }
  if (state.kind === "error") {
    return <p className="text-red-600">Backend unreachable: {state.message}</p>;
  }
  return (
    <ul className="space-y-1">
      <li>
        API: <strong>{state.health.status}</strong>
      </li>
      <li>
        Database: <strong>{state.health.database}</strong>
      </li>
    </ul>
  );
}
