export function statusToProgress(status?: string | null): number {
  switch (status) {
    case "pending": return 25;
    case "in_progress": return 50;
    case "completed": return 100;
    case "failed": return 100;
    default: return 10;
  }
}
