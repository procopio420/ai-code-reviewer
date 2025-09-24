import { useMemo } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTheme } from "next-themes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LANGUAGES, type Language, type Review } from "@/lib/types";
import ReviewCard from "./ReviewCard";

type CodeInputProps = {
  language: Language;
  code: string;
  onLanguage: (l: Language) => void;
  onCode: (v: string) => void;
  result?: Review;
  onSubmit: () => void;
  loading: boolean;
}

export default function CodeInput({
  language,
  code,
  onLanguage,
  onCode,
  result,
  onSubmit,
  loading
}: CodeInputProps) {
  const prismLang = useMemo(() => language?.value === "csharp" ? "cs" : language?.value, [language]);
  const { theme } = useTheme();

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <Card>
        <CardHeader><CardTitle>Input</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          <div className="grid gap-1.5">
            <Label>Language</Label>
            <Select value={language?.value} onValueChange={(value) => onLanguage(LANGUAGES.find(lang => lang?.value === value) || LANGUAGES[0])}>
              <SelectTrigger>
                <SelectValue placeholder="Pick a language" />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map(lang => <SelectItem key={lang?.value} value={lang?.value}>{lang?.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-1.5">
            <Label>Code</Label>
            <Textarea value={code} onChange={(e) => onCode(e?.target?.value)} placeholder="Paste your snippet here..." className="min-h-[220px]" />
          </div>
          <div className="flex justify-end items-center gap-3">
            <Button onClick={onSubmit} disabled={loading || !code?.trim()}>Submit</Button>
          </div>
        </CardContent>
      </Card>
      {result ? (
        <ReviewCard review={result} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
          </CardHeader>
          <CardContent className="overflow-auto">
            <SyntaxHighlighter language={prismLang} style={theme === "light" ? oneLight : oneDark} customStyle={{ background: "transparent", margin: 0 }}>
              {code || "// code preview"}
            </SyntaxHighlighter>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
