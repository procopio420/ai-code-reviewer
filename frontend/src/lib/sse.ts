import type { Review, ReviewStatus } from './types';

function isReviewStatus(x: unknown): x is ReviewStatus {
  return typeof x === 'string' && ['pending','in_progress','completed','failed'].includes(x);
}

function isReview(x: unknown): x is Review {
  return typeof x === 'object' && x !== null && 'id' in x && 'status' in x;
}

export function connectReviewStream(
  url: string,
  onStatus: (s: ReviewStatus) => void,
  onDone: (r: Review) => void,
  onError: (msg: string) => void,
): () => void {
  const es = new EventSource(url, { withCredentials: false });

  es.addEventListener('status', (ev) => {
    try {
      const data = JSON.parse((ev as MessageEvent).data) as unknown;
      if (isReviewStatus(data)) onStatus(data);
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Invalid status payload');
    }
  });

  es.addEventListener('done', (ev) => {
    try {
      const data = JSON.parse((ev as MessageEvent).data) as unknown;
      if (isReview(data)) onDone(data);
    } catch (e) {
      onError(e instanceof Error ? e.message : 'Invalid done payload');
    } finally {
      es.close();
    }
  });

  es.addEventListener('error', (ev) => {
    try {
      const data = JSON.parse((ev as MessageEvent).data) as unknown;
      onError(typeof data === 'string' ? data : 'Stream error');
    } catch {
      onError('Stream error');
    }
  });

  return () => es.close();
}
