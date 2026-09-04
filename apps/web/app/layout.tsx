import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrustLake",
  description:
    "TrustLake — a data professional's workspace, from raw data to trusted analysis and machine-learning predictions.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
