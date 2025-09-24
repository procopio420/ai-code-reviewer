import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner"
import CodeInput from "@/components/CodeInput";
import LiveQueue from "@/components/LiveQueue";
import { useReviewSSE } from "@/hooks/useReviewSSE";
import { submitReview, getReview, listReviews } from "@/lib/api";
import type { Language, Review } from "@/lib/types";

export default function Submit() {
  const queryClient = useQueryClient();

  const [language, setLanguage] = useState<Language>({ value: "python", label: "Python" });
  const [code, setCode] = useState("");

  const [id, setId] = useState<string | null>(null);
  const { status, done } = useReviewSSE(id ?? undefined);

  async function onSubmit() {
    setId(null);
    await submitMutation.mutateAsync({ language: language.value, code });
  }

  const liveQueueQuery = useQuery<Review[], Error>({
    queryKey: ["reviews"],
    queryFn: () => listReviews({ page_size: 5 })
  });

  const reviewResultQuery = useQuery<Review, Error>({
    queryKey: ["reviews", id, status],
    queryFn: () => getReview(id ?? ""),
    enabled: !!id,
  })

  const submitMutation = useMutation({
    mutationFn: submitReview,
    onMutate: async (payload: { language: string; code: string }) => {
      await queryClient.cancelQueries({ queryKey: ["reviews"] });

      const previous = queryClient.getQueryData<Review[]>(["reviews"]) ?? [];

      const tempId = `temp-${Date.now()}`;
      const optimistic: Review = {
        id: tempId,
        language: payload.language,
        status: "pending",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        score: null,
        issues: [],
        security: [],
        performance: [],
        suggestions: [],
        error: null,
      };

      queryClient.setQueryData<Review[]>(["reviews"], (old) => {
        const base = old ?? [];
        return [optimistic, ...base].slice(0, 5);
      });

      return { previous, tempId };
    },
    onSuccess: (res, _payload, ctx) => {
      setId(res.id);

      queryClient.setQueryData<Review[]>(["reviews"], (old) => {
        const list = old ?? [];
        return list.map((r) =>
          r.id === ctx?.tempId ? { ...r, id: res.id, status: res.status } : r
        );
      });
    },
    onError: (err, _payload, ctx) => {
      if (ctx) {
        queryClient.setQueryData<Review[]>(["reviews"], ctx.previous);
      }
      const msg = err instanceof Error ? err.message : "Submit failed";
      console.log('aqui?', err?.message)
      const causedByRateLimit = msg?.includes("429")
      if (causedByRateLimit) {
        toast("Slow down a bit", {
          position: "top-center",
          description: "You submitted reviews too quickly. The limit resets each hour.",
        });
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
    },
  });

  useEffect(() => {
    if (!id) return;
    if (done) {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
    }
  }, [id, done, queryClient]);

  return (
    <div className="grid-gap w-full px-5">
      <CodeInput
        onSubmit={onSubmit}
        loading={submitMutation?.isPending}
        result={reviewResultQuery?.data}
        language={language}
        onLanguage={(l) => {
          setLanguage(l);
          setId(null);
        }}
        code={code}
        onCode={(c) => {
          setCode(c);
          setId(null)
        }}
      />

      {!!liveQueueQuery?.data?.length && <LiveQueue items={liveQueueQuery?.data} />}
    </div>
  );
}
