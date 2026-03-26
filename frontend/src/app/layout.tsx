import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "NATAPrep 2026 — AI-Powered NATA Preparation",
  description: "Adaptive AI platform for NATA 2026. Score 120/120 with personalized learning.",
  keywords: ["NATA", "NATA preparation", "architecture exam", "adaptive learning"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
