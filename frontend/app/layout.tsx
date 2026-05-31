import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tumelo | AI Portfolio Twin",
  description: "Interactive AI profile assistant showcasing Tumelo's projects, technical decisions, and production deployment experience.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
