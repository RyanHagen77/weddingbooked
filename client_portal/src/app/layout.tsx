import "./globals.css";
import { AuthProvider } from "../components/AuthContext";
import React from "react";

import { Inter, Cormorant_Garamond, Libre_Franklin } from "next/font/google";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" }); // optional, not currently mapped
const display = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-display",
});
const sans = Libre_Franklin({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-sans",
});

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="bg-white">
      <body
        className={`${inter.variable} ${display.variable} ${sans.variable} font-body antialiased text-neutral-900`}
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
