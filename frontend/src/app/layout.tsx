import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "@/components/providers";
import Sidebar from "@/components/Sidebar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "AI Meeting Agent — Enterprise Intelligence Dashboard",
  description: "Enterprise Meeting & Channel Intelligence Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <div className="flex flex-col md:flex-row min-h-screen bg-slate-50/50">
            <Sidebar />
            <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
              <div className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
