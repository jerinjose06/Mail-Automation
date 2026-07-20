import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Local Email Agent",
  description: "AI Email Assistant Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} antialiased`} style={{ colorScheme: "dark" }}>
      <body className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-indigo-500/30">
        {children}
      </body>
    </html>
  );
}
