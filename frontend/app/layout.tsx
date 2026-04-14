import type { Metadata } from "next";
import "./globals.css";
import Header from "../components/Header";

export const metadata: Metadata = {
  title: "Meeting Notes Assistant",
  description: "Upload audio or video and get structured meeting notes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "Arial, sans-serif",
          background: "#f7f7f8",
          color: "#111827",
        }}
      >
        <Header />
        <main
          style={{
            maxWidth: 1080,
            margin: "0 auto",
            padding: "24px 16px 40px",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
