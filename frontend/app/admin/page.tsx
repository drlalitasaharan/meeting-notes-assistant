"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { CSSProperties } from "react";

import {
  AdminApiError,
  getAdminMeetings,
  getAdminOverview,
  getAdminSystemHealth,
} from "../../lib/admin-api";
import type {
  AdminMeeting,
  AdminMeetingsResponse,
  AdminOverview,
  AdminSystemHealth,
} from "../../lib/admin-api";

const AUTH_TOKEN_KEY = "meeting-notes-assistant-token";
const PAGE_SIZE = 20;

const cardStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid #d7e5db",
  borderRadius: 18,
  padding: 22,
  boxShadow: "0 8px 24px rgba(31, 90, 67, 0.07)",
};

const buttonStyle: CSSProperties = {
  minHeight: 42,
  padding: "10px 16px",
  border: "none",
  borderRadius: 12,
  background: "#2f6f4e",
  color: "#ffffff",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle: CSSProperties = {
  ...buttonStyle,
  background: "#ffffff",
  color: "#2f6f4e",
  border: "1px solid #9fc3aa",
};

const fieldStyle: CSSProperties = {
  width: "100%",
  minHeight: 42,
  border: "1px solid #b9d0c0",
  borderRadius: 12,
  padding: "10px 12px",
  background: "#ffffff",
  color: "#123326",
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat().format(value);
}

function formatDate(value: string | null): string {
  if (!value) return "—";

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function formatStatus(value: string): string {
  return (value || "unknown")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusStyle(status: string): CSSProperties {
  const normalized = status.toLowerCase();

  if (
    ["ok", "done", "complete", "completed", "success", "succeeded"].includes(
      normalized,
    )
  ) {
    return {
      color: "#166534",
      background: "#e8f7ed",
      border: "1px solid #bbdfc5",
    };
  }

  if (["failed", "failure", "error"].includes(normalized)) {
    return {
      color: "#991b1b",
      background: "#fef2f2",
      border: "1px solid #fecaca",
    };
  }

  if (
    [
      "processing",
      "running",
      "in_progress",
      "transcribing",
      "summarizing",
    ].includes(normalized)
  ) {
    return {
      color: "#1d4ed8",
      background: "#eff6ff",
      border: "1px solid #bfdbfe",
    };
  }

  return {
    color: "#92400e",
    background: "#fffbeb",
    border: "1px solid #fde68a",
  };
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <article style={{ ...cardStyle, padding: 18, minHeight: 125 }}>
      <p
        style={{
          margin: 0,
          color: "#5e7466",
          fontSize: 12,
          fontWeight: 800,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {label}
      </p>

      <p
        style={{
          margin: "14px 0 0",
          color: "#123326",
          fontSize: 30,
          fontWeight: 800,
        }}
      >
        {value}
      </p>

      {detail ? (
        <p
          style={{
            margin: "8px 0 0",
            color: "#6b7f73",
            fontSize: 13,
          }}
        >
          {detail}
        </p>
      ) : null}
    </article>
  );
}

export default function AdminPage() {
  const router = useRouter();

  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [meetings, setMeetings] =
    useState<AdminMeetingsResponse | null>(null);
  const [health, setHealth] = useState<AdminSystemHealth | null>(null);

  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isForbidden, setIsForbidden] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboard = useCallback(
    async (initial = false) => {
      if (initial) {
        setIsLoading(true);
      }

      setIsRefreshing(true);
      setError(null);

      try {
        const [overviewData, meetingData, healthData] =
          await Promise.all([
            getAdminOverview(),
            getAdminMeetings({
              search,
              status: statusFilter,
              limit: PAGE_SIZE,
              offset: page * PAGE_SIZE,
            }),
            getAdminSystemHealth(),
          ]);

        setOverview(overviewData);
        setMeetings(meetingData);
        setHealth(healthData);
        setIsForbidden(false);
        setLastUpdated(new Date());
      } catch (err) {
        if (err instanceof AdminApiError && err.status === 401) {
          window.localStorage.removeItem(AUTH_TOKEN_KEY);
          router.replace("/login?next=/admin");
          return;
        }

        if (err instanceof AdminApiError && err.status === 403) {
          setIsForbidden(true);
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Admin monitoring is temporarily unavailable.",
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [page, router, search, statusFilter],
  );

  useEffect(() => {
    void loadDashboard(true);
  }, [loadDashboard]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        void loadDashboard(false);
      }
    }, 60_000);

    return () => window.clearInterval(interval);
  }, [loadDashboard]);

  const statuses = useMemo(
    () => Object.keys(overview?.status_counts ?? {}).sort(),
    [overview],
  );

  const totalPages = Math.max(
    1,
    Math.ceil((meetings?.total ?? 0) / PAGE_SIZE),
  );

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(0);
    setSearch(searchInput.trim());
  }

  if (isLoading) {
    return (
      <section style={{ ...cardStyle, maxWidth: 760 }}>
        Verifying admin access and loading monitoring data...
      </section>
    );
  }

  if (isForbidden) {
    return (
      <section
        style={{
          ...cardStyle,
          maxWidth: 760,
          background: "#fffafa",
          borderColor: "#fecaca",
        }}
      >
        <h1 style={{ margin: 0, color: "#991b1b" }}>
          Admin access required
        </h1>

        <p style={{ color: "#4b5563", lineHeight: 1.6 }}>
          This private page is available only to authorized MeetIQ
          administrators.
        </p>

        <Link
          href="/meetings"
          style={{
            ...secondaryButtonStyle,
            display: "inline-block",
            textDecoration: "none",
          }}
        >
          Return to meetings
        </Link>
      </section>
    );
  }

  if (error && (!overview || !meetings || !health)) {
    return (
      <section
        style={{
          ...cardStyle,
          maxWidth: 760,
          background: "#fffafa",
          borderColor: "#fecaca",
        }}
      >
        <h1 style={{ margin: 0, color: "#991b1b" }}>
          Admin monitoring unavailable
        </h1>

        <p style={{ color: "#4b5563", lineHeight: 1.6 }}>{error}</p>

        <button
          type="button"
          onClick={() => void loadDashboard(true)}
          style={buttonStyle}
        >
          Try again
        </button>
      </section>
    );
  }

  if (!overview || !meetings || !health) {
    return null;
  }

  return (
    <div
      style={{
        display: "grid",
        gap: 22,
        width: "100%",
        maxWidth: 1240,
      }}
    >
      <section
        style={{
          ...cardStyle,
          background:
            "linear-gradient(135deg, #f8fff9 0%, #eef7ef 100%)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 18,
            flexWrap: "wrap",
          }}
        >
          <div>
            <p
              style={{
                margin: 0,
                color: "#2f6f4e",
                fontSize: 12,
                fontWeight: 800,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              Private operations
            </p>

            <h1
              style={{
                margin: "8px 0 0",
                color: "#123326",
                fontSize: 38,
              }}
            >
              Admin monitoring
            </h1>

            <p
              style={{
                margin: "12px 0 0",
                color: "#4f6b5b",
                lineHeight: 1.6,
              }}
            >
              Monitor product usage, meeting processing, failures, stuck
              jobs, and platform health.
            </p>
          </div>

          <div style={{ textAlign: "right" }}>
            <button
              type="button"
              onClick={() => void loadDashboard(false)}
              disabled={isRefreshing}
              style={{
                ...buttonStyle,
                opacity: isRefreshing ? 0.6 : 1,
              }}
            >
              {isRefreshing ? "Refreshing..." : "Refresh"}
            </button>

            <p
              style={{
                margin: "9px 0 0",
                color: "#6b7f73",
                fontSize: 13,
              }}
            >
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()}`
                : ""}
            </p>
          </div>
        </div>
      </section>

      {error ? (
        <section
          style={{
            padding: 14,
            borderRadius: 12,
            border: "1px solid #fecaca",
            background: "#fff7f7",
            color: "#991b1b",
          }}
        >
          Refresh failed. Existing dashboard information is still shown.
          {" "}
          {error}
        </section>
      ) : null}

      <section
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(165px, 1fr))",
          gap: 14,
        }}
      >
        <Metric
          label="Total users"
          value={formatNumber(overview.total_users)}
        />
        <Metric
          label="Total meetings"
          value={formatNumber(overview.total_meetings)}
        />
        <Metric
          label="Today"
          value={formatNumber(overview.meetings_today)}
        />
        <Metric
          label="Last 7 days"
          value={formatNumber(overview.meetings_last_7_days)}
        />
        <Metric
          label="Completed"
          value={formatNumber(overview.completed)}
        />
        <Metric
          label="Failed"
          value={formatNumber(overview.failed)}
        />
        <Metric
          label="Active"
          value={formatNumber(
            overview.processing + overview.queued,
          )}
          detail={`${overview.processing} processing · ${overview.queued} queued`}
        />
        <Metric
          label="Stuck"
          value={formatNumber(overview.stuck)}
          detail={`Over ${overview.stuck_after_minutes} minutes`}
        />
        <Metric
          label="Success rate"
          value={
            overview.success_rate_percent === null
              ? "—"
              : `${overview.success_rate_percent}%`
          }
        />
      </section>

      <section style={cardStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 14,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <div>
            <p
              style={{
                margin: 0,
                color: "#2f6f4e",
                fontWeight: 800,
                fontSize: 12,
                textTransform: "uppercase",
              }}
            >
              Infrastructure
            </p>
            <h2 style={{ margin: "7px 0 0", color: "#123326" }}>
              System health
            </h2>
          </div>

          <span
            style={{
              ...statusStyle(health.status),
              borderRadius: 999,
              padding: "7px 12px",
              fontWeight: 800,
              textTransform: "capitalize",
            }}
          >
            {health.status}
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 14,
            marginTop: 18,
          }}
        >
          {Object.entries(health.checks ?? {}).map(
            ([name, check]) => (
              <article
                key={name}
                style={{
                  border: "1px solid #d7e5db",
                  background: "#f9fcfa",
                  borderRadius: 14,
                  padding: 16,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                  }}
                >
                  <strong
                    style={{
                      color: "#123326",
                      textTransform: "capitalize",
                    }}
                  >
                    {name}
                  </strong>

                  <span
                    style={{
                      ...statusStyle(check.status),
                      borderRadius: 999,
                      padding: "4px 9px",
                      fontSize: 12,
                      fontWeight: 800,
                    }}
                  >
                    {check.status}
                  </span>
                </div>

                {check.detail ? (
                  <p
                    style={{
                      margin: "10px 0 0",
                      color: "#64766b",
                      fontSize: 13,
                      overflowWrap: "anywhere",
                    }}
                  >
                    {check.detail}
                  </p>
                ) : null}
              </article>
            ),
          )}
        </div>
      </section>

      <section style={cardStyle}>
        <p
          style={{
            margin: 0,
            color: "#2f6f4e",
            fontWeight: 800,
            fontSize: 12,
            textTransform: "uppercase",
          }}
        >
          Processing activity
        </p>

        <h2 style={{ margin: "7px 0 0", color: "#123326" }}>
          Meeting monitor
        </h2>

        <form
          onSubmit={submitSearch}
          style={{
            display: "grid",
            gridTemplateColumns:
              "minmax(230px, 1fr) minmax(160px, 220px) auto auto",
            gap: 10,
            marginTop: 18,
            alignItems: "end",
          }}
        >
          <label
            style={{
              display: "grid",
              gap: 6,
              color: "#244c38",
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            Search
            <input
              value={searchInput}
              onChange={(event) =>
                setSearchInput(event.target.value)
              }
              placeholder="Meeting title or user email"
              style={fieldStyle}
            />
          </label>

          <label
            style={{
              display: "grid",
              gap: 6,
              color: "#244c38",
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            Status
            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setPage(0);
              }}
              style={fieldStyle}
            >
              <option value="">All statuses</option>
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {formatStatus(status)}
                </option>
              ))}
            </select>
          </label>

          <button type="submit" style={buttonStyle}>
            Search
          </button>

          <button
            type="button"
            onClick={() => {
              setSearchInput("");
              setSearch("");
              setPage(0);
            }}
            style={secondaryButtonStyle}
          >
            Clear
          </button>
        </form>

        <p
          style={{
            margin: "15px 0 0",
            color: "#64766b",
            fontSize: 14,
          }}
        >
          Showing {meetings.items.length} of{" "}
          {formatNumber(meetings.total)} matching meetings.
        </p>

        <div
          style={{
            overflowX: "auto",
            marginTop: 15,
            border: "1px solid #d7e5db",
            borderRadius: 14,
          }}
        >
          <table
            style={{
              width: "100%",
              minWidth: 920,
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr style={{ background: "#f1f7f3" }}>
                {[
                  "Uploaded",
                  "Meeting",
                  "User",
                  "Status",
                  "Updated",
                  "Error",
                  "Stuck",
                ].map((heading) => (
                  <th
                    key={heading}
                    style={{
                      padding: 13,
                      textAlign: "left",
                      color: "#365744",
                      fontSize: 12,
                      textTransform: "uppercase",
                      borderBottom: "1px solid #d7e5db",
                    }}
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {meetings.items.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{
                      padding: 28,
                      textAlign: "center",
                      color: "#64766b",
                    }}
                  >
                    No meetings match the selected filters.
                  </td>
                </tr>
              ) : (
                meetings.items.map((meeting: AdminMeeting) => (
                  <tr key={meeting.id}>
                    <td style={cellStyle}>
                      {formatDate(meeting.created_at)}
                    </td>

                    <td style={cellStyle}>
                      <strong style={{ color: "#123326" }}>
                        {meeting.title || `Meeting ${meeting.id}`}
                      </strong>
                      <div
                        style={{
                          marginTop: 4,
                          color: "#7a8b80",
                          fontSize: 12,
                        }}
                      >
                        ID {meeting.id}
                      </div>
                    </td>

                    <td
                      style={{
                        ...cellStyle,
                        overflowWrap: "anywhere",
                      }}
                    >
                      {meeting.user_email ?? "Unassigned"}
                    </td>

                    <td style={cellStyle}>
                      <span
                        style={{
                          ...statusStyle(meeting.status),
                          display: "inline-flex",
                          borderRadius: 999,
                          padding: "6px 10px",
                          fontSize: 12,
                          fontWeight: 800,
                        }}
                      >
                        {formatStatus(meeting.status)}
                      </span>
                    </td>

                    <td style={cellStyle}>
                      {formatDate(meeting.updated_at)}
                    </td>

                    <td
                      title={meeting.last_error ?? undefined}
                      style={{
                        ...cellStyle,
                        color: meeting.last_error
                          ? "#991b1b"
                          : "#64766b",
                        maxWidth: 260,
                        overflowWrap: "anywhere",
                      }}
                    >
                      {meeting.last_error ?? "—"}
                    </td>

                    <td style={cellStyle}>
                      {meeting.is_stuck ? (
                        <strong style={{ color: "#9a3412" }}>
                          Yes
                        </strong>
                      ) : (
                        "No"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
            flexWrap: "wrap",
            marginTop: 18,
          }}
        >
          <p style={{ margin: 0, color: "#64766b" }}>
            Page {page + 1} of {totalPages}
          </p>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              type="button"
              disabled={page === 0}
              onClick={() =>
                setPage((current) => Math.max(0, current - 1))
              }
              style={{
                ...secondaryButtonStyle,
                opacity: page === 0 ? 0.5 : 1,
              }}
            >
              Previous
            </button>

            <button
              type="button"
              disabled={page + 1 >= totalPages}
              onClick={() =>
                setPage((current) =>
                  Math.min(totalPages - 1, current + 1),
                )
              }
              style={{
                ...secondaryButtonStyle,
                opacity: page + 1 >= totalPages ? 0.5 : 1,
              }}
            >
              Next
            </button>
          </div>
        </div>
      </section>

      <p
        style={{
          margin: 0,
          color: "#718078",
          fontSize: 13,
          textAlign: "center",
        }}
      >
        This private dashboard refreshes every 60 seconds while the tab is
        active.
      </p>
    </div>
  );
}

const cellStyle: CSSProperties = {
  padding: 13,
  color: "#52685a",
  fontSize: 13,
  borderBottom: "1px solid #edf2ee",
  verticalAlign: "top",
};
