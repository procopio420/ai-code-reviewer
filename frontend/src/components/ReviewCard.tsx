import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import type { Review } from "@/lib/types";
import { statusToProgress } from "@/lib/progress";
import { useMemo } from "react";

export default function ReviewCard({ review, marginTop }: { review: Review, marginTop?: number }) {
  const statusClass = useMemo(() => (
    review?.status === "completed" ? "bg-emerald-500/15 text-emerald-300 border-emerald-700/40" :
      review?.status === "failed" ? "bg-rose-500/15 text-rose-300 border-rose-700/40" :
        "bg-blue-500/15 text-blue-300 border-blue-700/40"
  ), [review?.status])

  const progressValue = useMemo(() => statusToProgress(review?.status), [review?.status])

  if (!review) {
    return null
  }

  return (
    <Card className={`mt-${marginTop}`}>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">Review {review.id?.slice(-6)}</CardTitle>
        <Badge className={statusClass}>{review.status}</Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Progress value={progressValue} />

        <div><b>Language:</b> {review.language}</div>
        <div><b>Score:</b> {review.score ?? "—"}</div>
        {!!review.error && <div className="text-rose-300"><b>Error:</b> {review.error}</div>}
        {!!review.issues?.length && (
          <>
            <Separator />
            <div>
              <b>Issues:</b>
              <ul className="mt-2 list-disc pl-5">
                {review.issues.map((it, i) => (
                  <li key={i}>
                    {it.title}{it.detail ? <span className="text-muted-foreground"> — {it.detail}</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
