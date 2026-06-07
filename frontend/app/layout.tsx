import type { Metadata } from "next";
import "./globals.css";
import Header from "../components/Header";

export const metadata: Metadata = {
  title: "MeetIQ by Acjen AI",
  description: "Upload audio or video meetings and get structured notes with AI-powered summaries and action items.",
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
          background: "linear-gradient(180deg, #f3fbf4 0%, #f8fbf8 45%, #ffffff 100%)",
          color: "#123326",
        }}
      >
        <Header />
        <main
          style={{
            maxWidth: 980,
            margin: "0 auto",
            padding: "18px 16px 28px",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
