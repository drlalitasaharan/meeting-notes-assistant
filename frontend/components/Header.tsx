"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAuthToken, subscribeToAuthChanges } from "../lib/api";

export default function Header() {
  const [loggedIn, setLoggedIn] = useState(false);
  const router = useRouter();

  useEffect(() => {
    function checkAuth() {
      try {
        const token = window.localStorage.getItem("meeting-notes-assistant-token");
        setLoggedIn(Boolean(token));
      } catch {
        setLoggedIn(false);
      }
    }

    checkAuth();
    const unsubscribe = subscribeToAuthChanges(checkAuth);
    return unsubscribe;
  }, []);

  function handleLogout() {
    clearAuthToken();
    setLoggedIn(false);
    router.push("/login");
  }

  return (
    <header
      style={{
        background: "rgba(251, 255, 251, 0.92)",
        borderBottom: "1px solid #cfe6d4",
      }}
    >
      <div
        style={{
          maxWidth: 1080,
          margin: "0 auto",
          padding: "14px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
        }}
      >
        <Link
          href="/upload"
          style={{
            textDecoration: "none",
            color: "#123326",
            fontWeight: 700,
            fontSize: 18,
          }}
        >
          MeetIQ by Acjen AI
        </Link>

        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
          {loggedIn ? (
            <>
              <Link
                href="/upload"
                style={{ textDecoration: "none", color: "#2f6f4e", fontWeight: 500 }}
              >
                New Upload
              </Link>
              <Link
                href="/meetings"
                style={{ textDecoration: "none", color: "#2f6f4e", fontWeight: 500 }}
              >
                Meetings
              </Link>
              <button
                onClick={handleLogout}
                style={{
                  background: "transparent",
                  border: "none",
                  padding: 0,
                  margin: 0,
                  color: "#2f6f4e",
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                style={{ textDecoration: "none", color: "#2f6f4e", fontWeight: 500 }}
              >
                Login
              </Link>
              <Link
                href="/signup"
                style={{
                  textDecoration: "none",
                  color: "#ffffff",
                  background: "#2f6f4e",
                  padding: "8px 14px",
                  borderRadius: "10px",
                  fontWeight: 500,
                }}
              >
                Create account
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
