import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "../components/AuthContext";
import React from "react"; // Ensure correct path

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
