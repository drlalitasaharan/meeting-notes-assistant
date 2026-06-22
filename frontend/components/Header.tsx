"use client";

import Link from "next/link";
import { useEffect, useState, type CSSProperties } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearAuthToken, subscribeToAuthChanges } from "../lib/api";

const navItemStyle: CSSProperties = {
  color: "#2f6f4e",
  fontFamily: "inherit",
  fontSize: 16,
  fontWeight: 700,
  lineHeight: "20px",
  textDecoration: "none",
  display: "inline-flex",
  alignItems: "center",
};

const activeNavItemStyle: CSSProperties = {
  ...navItemStyle,
  background: "#e7f7ed",
  borderRadius: 999,
  color: "#123326",
  padding: "8px 12px",
};

const logoutButtonStyle: CSSProperties = {
  ...navItemStyle,
  background: "transparent",
  border: "none",
  padding: 0,
  margin: 0,
  cursor: "pointer",
  appearance: "none",
  WebkitAppearance: "none",
};

const loggedInNavItems = [
  { href: "/upload", label: "New Upload" },
  { href: "/meetings", label: "Meetings" },
  { href: "/usage", label: "Usage" },
  { href: "/account", label: "Account" },
  { href: "/pricing", label: "Pricing" },
  { href: "/support", label: "Support" },
];

function isActivePath(pathname: string, href: string): boolean {
  if (href === "/meetings") {
    return pathname === "/meetings" || pathname.startsWith("/meetings/");
  }

  return pathname === href;
}

export default function Header() {
  const [loggedIn, setLoggedIn] = useState(false);
  const pathname = usePathname();
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
        className="app-header-inner"
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
          className="app-header-brand"
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

        <nav
          className="app-header-nav"
          style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}
        >
          {loggedIn ? (
            <>
              {loggedInNavItems.map((item) => {
                const active = isActivePath(pathname, item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    style={active ? activeNavItemStyle : navItemStyle}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <button type="button" onClick={handleLogout} style={logoutButtonStyle}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/pricing" style={navItemStyle}>
                Pricing
              </Link>
              <Link href="/login" style={navItemStyle}>
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
