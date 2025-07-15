import "./globals.css";
import { AuthProvider } from "../components/AuthContext";
import React from "react";

// ✅ Import fonts only once
import { Inter, Cormorant_Garamond, Libre_Franklin } from "next/font/google";

// ✅ Declare all font variables
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
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
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* ✅ Apply all font variables to body */}
      <body className={`${inter.variable} ${display.variable} ${sans.variable}`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
