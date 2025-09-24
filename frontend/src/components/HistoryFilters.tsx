import * as React from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import type { DateRange } from "react-day-picker";

const LANGS = [
  "python",
  "javascript",
  "typescript",
  "go",
  "java",
  "csharp",
  "rust",
  "ruby",
  "php",
  "cpp",
] as const;

type LanguageFilter = "all" | (typeof LANGS)[number];

export type HistoryFilterValue = {
  language: LanguageFilter;
  scoreRange?: [number, number];
  date?: DateRange;
};

type HistoryFilterProps = {
  value: HistoryFilterValue;
  onChange: (v: HistoryFilterValue) => void;
  onApply: () => void;
  onReset?: () => void;
};

export function HistoryFilters({ value, onChange, onApply, onReset }: HistoryFilterProps) {
  const onLang = (v: LanguageFilter) => onChange({ ...value, language: v });
  const onScore = (v: number[]) => {
    const min = Math.max(0, Math.min(10, Math.round(v[0] ?? 0)));
    const max = Math.max(0, Math.min(10, Math.round(v[1] ?? 10)));
    onChange({ ...value, scoreRange: [Math.min(min, max), Math.max(min, max)] as [number, number] });
  };
  const onDate = (range: DateRange) => onChange({ ...value, date: { from: range?.from, to: range?.to } });

  const labelDate = React.useMemo(() => {
    const f = value.date?.from;
    const t = value.date?.to;
    if (f && t) return `${format(f, "yyyy-MM-dd")} → ${format(t, "yyyy-MM-dd")}`;
    if (f) return `${format(f, "yyyy-MM-dd")} → …`;
    return "date range";
  }, [value.date]);

  return (
    <div className="w-full grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
      <div className="space-y-1">
        <label className="text-sm text-muted-foreground">Language</label>
        <Select value={value.language} onValueChange={onLang}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="language..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All languages</SelectItem>
            {LANGS.map(l => (
              <SelectItem key={l} value={l}>{l}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2 col-span-1 md:col-span-2">
        <label className="text-sm text-muted-foreground">Score range</label>
        <div className="px-2">
          <Slider
            value={[(value.scoreRange?.[0] ?? 0), (value.scoreRange?.[1] ?? 10)]}
            min={0}
            max={10}
            step={1}
            onValueChange={onScore}
          />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>min: {value.scoreRange?.[0] ?? 0}</span>
          <span>max: {value.scoreRange?.[1] ?? 10}</span>
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-sm text-muted-foreground">Date range</label>
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className={cn("w-full justify-start text-left font-normal")}>
              <CalendarIcon className="mr-2 h-4 w-4" />
              {labelDate}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="end">
            <Calendar
              required={false}
              mode="range"
              numberOfMonths={2}
              selected={value.date}
              onSelect={(range: DateRange | undefined) => range && onDate(range)}
            />
            <div className="flex justify-between p-2">
              <Button variant="ghost" size="sm" onClick={() => onChange({ ...value, date: undefined })}>
                Clear
              </Button>
              <Button size="sm" onClick={onApply}>Apply</Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <div className="md:col-span-4 flex gap-2">
        <Button onClick={onApply}>Apply filters</Button>
        <Button variant="secondary" onClick={onReset}>Reset</Button>
      </div>
    </div>
  );
}
