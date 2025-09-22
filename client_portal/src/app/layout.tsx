import "./globals.css";
import { AuthProvider } from "../components/AuthContext";
import React from "react";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="bg-white">
      <head>
        {/* Adobe Fonts (Typekit) */}
        <link rel="stylesheet" href="https://use.typekit.net/mnr1fsy.css" />
      </head>
      {/* Use your CSS helper class for the default body font */}
      <body className="font-gothic antialiased text-neutral-900">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
