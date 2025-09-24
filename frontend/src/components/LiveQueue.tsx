import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Review, ReviewStatus } from "@/lib/types";
import { Separator } from "@radix-ui/react-select";
import { NavLink } from "react-router-dom";

function StatusBadge({ status }: { status: ReviewStatus }) {
  const cls =
    status === "completed" ? "bg-emerald-500/15 text-emerald-300 border-emerald-700/40" :
    status === "failed" ? "bg-rose-500/15 text-rose-300 border-rose-700/40" :
    "bg-blue-500/15 text-blue-300 border-blue-700/40";
  return <Badge className={cls}>{status}</Badge>;
}

function LiveItem({ item }: { item: Review }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <CardTitle className="text-base">#{item.id.slice(-6)} — {item.language}</CardTitle>
        <StatusBadge status={item?.status} />
      </CardHeader>
      <CardContent className="space-y-3">
        <div><b>Language:</b> {item.language}</div>
        <div><b>Score:</b> {item.score ?? "—"}</div>
        {item.error && <div className="text-rose-300"><b>Error:</b> {item.error}</div>}
        {!!item.issues?.length && (
          <>
            <Separator />
            <div>
              <b>Issues:</b>
              <ul className="mt-2 list-disc pl-5">
                {item.issues.map((it, i) => (
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

export default function LiveQueue({ items }: { items: Review[] }) {
  if (!items.length) return null;
  return (
    <div className="grid-gap">
      <h2 className="text-lg font-bold my-2">Last 5 submissions <NavLink to="/history">(Click here to see more)</NavLink></h2>
      <div className="grid md:grid-cols-1 gap-4">
        {items.map((it) => (
          <LiveItem key={it.id} item={it} />
        ))}
      </div>
    </div>
  );
}
