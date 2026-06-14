import type { Metadata } from "next";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "OmniWrite — AI-Powered Content Creation",
  description:
    "Generate brand-aligned content across Blog, LinkedIn, and Reddit with an intelligent multi-agent system.",
  keywords: ["AI content", "content generation", "blog writing", "LinkedIn content", "Reddit posts"],
  openGraph: {
    title: "OmniWrite — AI-Powered Content Creation",
    description: "Generate brand-aligned content across platforms with intelligent AI agents.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OmniWrite — AI Content Generation",
    description: "Generate brand-aligned content with intelligent AI agents.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
