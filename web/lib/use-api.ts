"use client";
import { useEffect, useState } from "react";
import { api } from "./api";

export function useApi<T>(path: string | null) {
  const [state, setState] = useState<{ key: string; data: T | null; error: string | null } | null>(null);
  const [tick, setTick] = useState(0);
  const key = path ? `${tick}:${path}` : "";
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    api<T>(path, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setState({ key, data, error: null });
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setState({ key, data: null, error: error.message });
      });
    return () => controller.abort();
  }, [path, key]);
  const current = state?.key === key ? state : null;
  return {
    data: current?.data ?? null, error: current?.error ?? null,
    loading: !!path && current === null, reload: () => setTick((value) => value + 1),
  };
}
