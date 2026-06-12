"use client";

import Link from "next/link";
import { useEffect, useState, type CSSProperties } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearAuthToken, subscribeToAuthChanges } from "../lib/api";

const navLinkBaseStyle: CSSProperties = {
  color: "#2f6f4e",
  fontWeight: 600,
  textDecoration: "none",
  paddingBottom: 3,
  borderBottom: "2px solid transparent",
};

function navLinkStyle(pathname: string, href: string): CSSProperties {
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return {
    ...navLinkBaseStyle,
    fontWeight: isActive ? 800 : 600,
    borderBottomColor: isActive ? "#2f6f4e" : "transparent",
  };
}

export default function Header() {
  const [loggedIn, setLoggedIn] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

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
              <Link href="/upload" style={navLinkStyle(pathname, "/upload")}>
                New Upload
              </Link>
              <Link href="/meetings" style={navLinkStyle(pathname, "/meetings")}>
                Meetings
              </Link>
              <Link href="/usage" style={navLinkStyle(pathname, "/usage")}>
                Usage
              </Link>
              <Link href="/support" style={navLinkStyle(pathname, "/support")}>
                Support
              </Link>
              <button
                onClick={handleLogout}
                style={{
                  background: "transparent",
                  border: "none",
                  padding: 0,
                  margin: 0,
                  color: "#2f6f4e",
                  fontWeight: 600,
                  cursor: "pointer",
                  font: "inherit",
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" style={navLinkStyle(pathname, "/login")}>
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
                  fontWeight: 700,
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
