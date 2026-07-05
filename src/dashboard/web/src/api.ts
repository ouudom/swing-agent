import { useCallback, useEffect, useState } from "react";

export type Row = Record<string, unknown>;

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(path);
  const json = await res.json();
  if (!json.ok) throw new Error(json.error || `request failed: ${path}`);
  return json.data as T;
}

// Poll a read-only endpoint on an interval. Returns { data, error, loading, updated }.
export function usePoll<T>(path: string, intervalMs = 45000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updated, setUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const d = await fetchApi<T>(path);
      setData(d);
      setError(null);
      setUpdated(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    load();
    const id = setInterval(load, intervalMs);
    return () => clearInterval(id);
  }, [load, intervalMs]);

  return { data, error, loading, updated, reload: load };
}

// --- shaped response types ---
export interface Health {
  routines: Row[];
  jobs: Row[];
  data_freshness: Row[];
  server_time: string;
}
export interface Pnl {
  overall: Row;
  by_instrument: Row[];
  recent: Row[];
}

// Fetch a single prose doc's full body on demand (not polled).
export async function getDoc(docType: string, key: string): Promise<Row | null> {
  const res = await fetch(`/api/doc?type=${encodeURIComponent(docType)}&key=${encodeURIComponent(key)}`);
  const json = await res.json();
  if (!json.ok) throw new Error(json.error || "doc fetch failed");
  return json.data as Row | null;
}
