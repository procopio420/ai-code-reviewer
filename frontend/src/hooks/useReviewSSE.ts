import type { Review } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

type DonePayload = { status: "completed" | "failed"; review?: Review };

export function useReviewSSE(id?: string) {
  const [status, setStatus] = useState<string | null>(null);
  const [done, setDone] = useState<DonePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!id) return;
    let gotDone = false;
    let closed = false;

    const url = `${import.meta.env.VITE_BACKEND_URL}/api/reviews/${id}/stream?interval_ms=800&ping=15000`;
    const es = new EventSource(url);
    esRef.current = es;

    const onStatus = (e: MessageEvent) => setStatus(e.data);
    const onDone = (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data) as DonePayload;
        setDone(payload);
        gotDone = true;
      } catch {
        setError("parse_error");
      } finally {
        if (!closed) {
          closed = true;
          es.close();
        }
      }
    };
    const onError = () => {
      if (!gotDone && !closed) setError("sse_error");
      if (!closed) {
        closed = true;
        es.close();
      }
    };

    es.addEventListener("status", onStatus);
    es.addEventListener("done", onDone);
    es.onerror = onError;

    return () => {
      es.removeEventListener("status", onStatus);
      es.removeEventListener("done", onDone);
      if (!closed) {
        closed = true;
        es.close();
      }
    };
  }, [id]);

  return { status, done, error };
}
