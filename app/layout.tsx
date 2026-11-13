import type { Metadata } from "next";
import "./globals.css";
import { CaveatStrip } from "@/components/CaveatStrip";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "Who Delivers Under Pressure? IPL & T20I, 2022 to 2026",
  description:
    "An audited empirical evaluation of batting and bowling performance in high-leverage corridors across 829 non-DLS matches. Descriptive historical ratings, not predictions.",
  metadataBase: new URL("https://pressure-xi.local"),
  openGraph: {
    title: "Who Delivers Under Pressure? IPL & T20I, 2022 to 2026",
    description:
      "Audited empirical evaluation of batting and bowling performance under pressure. Descriptive historical ratings.",
    siteName: "Pressure XI",
    type: "website",
  },
  robots: {
    index: false,
    follow: false,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-canvas text-text-primary antialiased min-h-screen flex flex-col">
        <CaveatStrip />
        <Navbar />
        <main role="main" className="flex-1 w-full">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
