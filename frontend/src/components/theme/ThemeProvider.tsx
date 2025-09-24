import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

export function ThemeProvider({
  children,
  defaultTheme = "dark",
  storageKey = "ui-theme",
}: React.PropsWithChildren<{ defaultTheme?: string; storageKey?: string }>) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme={defaultTheme}
      enableSystem
      storageKey={storageKey}
    >
      {children}
    </NextThemesProvider>
  );
}
