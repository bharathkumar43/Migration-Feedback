import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import MetricsCard from "../components/MetricsCard";
import Leaderboard from "../components/Leaderboard";
import { getDashboardSummary, getRecentFeedbacks, getDailyTrends, adminLogin } from "../api/api";

const REFRESH_INTERVAL_MS = 3 * 60 * 1000; // 3 minutes

function LoginForm({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data = await adminLogin(username, password);
      sessionStorage.setItem("admin_token", data.token);
      sessionStorage.setItem("admin_username", data.username);
      sessionStorage.setItem("admin_display_name", data.display_name);
      onLogin();
    } catch (err) {
      setError(err.message || "Invalid credentials");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="feedback-container">
      <form className="feedback-card" onSubmit={handleSubmit}>
        <h2>Admin Login</h2>
        <p style={{ marginBottom: 24 }}>Sign in to view the dashboard</p>
        {error && <p style={{ color: "var(--color-danger)", marginBottom: 16 }}>{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="comment-box"
          style={{ minHeight: "auto", marginBottom: 12 }}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="comment-box"
          style={{ minHeight: "auto", marginBottom: 20 }}
          required
        />
        <button type="submit" className="submit-btn" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign In"}
        </button>
        <p style={{ marginTop: 16, fontSize: 14, color: "var(--color-text-muted)" }}>
          Don't have an account?{" "}
          <Link to="/signup" style={{ color: "var(--color-primary)", textDecoration: "none", fontWeight: 600 }}>
            Sign Up
          </Link>
        </p>
      </form>
    </div>
  );
}

function FeedbackTable({ items }) {
  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th>Customer Email</th>
          <th>Rating</th>
          <th>Comment</th>
          <th>Migration Manager</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {items.map((fb) => (
          <tr key={fb.id}>
            <td style={{ fontWeight: 500 }}>{fb.customer_email}</td>
            <td>
              <span className="rating-stars">
                {"\u2605".repeat(fb.rating)}
                {"\u2606".repeat(5 - fb.rating)}
              </span>{" "}
              <span style={{ fontWeight: 600 }}>{fb.rating}/5</span>
            </td>
            <td style={{ maxWidth: 300, color: fb.comment ? "var(--color-text)" : "var(--color-text-muted)" }}>
              {fb.comment || "No comment"}
            </td>
            <td>{fb.mm_email || "—"}</td>
            <td style={{ whiteSpace: "nowrap", fontSize: 13 }}>
              {fb.created_at
                ? new Date(fb.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TrendLineChart({ trends, maxRating }) {
  const [tooltip, setTooltip] = useState(null);
  const svgRef = useRef(null);
  const padding = { top: 30, right: 40, bottom: 40, left: 45 };
  const width = 700;
  const height = 260;
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const minR = 0;
  const maxR = maxRating;
  const points = trends.map((t, i) => {
    const x = padding.left + (trends.length === 1 ? chartW / 2 : (i / (trends.length - 1)) * chartW);
    const y = padding.top + chartH - ((t.average_rating - minR) / (maxR - minR)) * chartH;
    return { x, y, ...t };
  });

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const areaPath = linePath + ` L${points[points.length - 1].x},${padding.top + chartH} L${points[0].x},${padding.top + chartH} Z`;

  const gridLines = [1, 2, 3, 4, 5];

  function handleDotEnter(p, e) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = rect.width / width;
    const scaleY = rect.height / height;
    setTooltip({
      left: p.x * scaleX,
      top: p.y * scaleY - 10,
      date: new Date(p.week).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" }),
      rating: p.average_rating,
      feedbacks: p.total_feedbacks,
    });
  }

  return (
    <div className="trend-chart-container" onMouseLeave={() => setTooltip(null)}>
      {tooltip && (
        <div className="chart-tooltip" style={{ left: tooltip.left, top: tooltip.top }}>
          <div className="chart-tooltip-date">{tooltip.date}</div>
          <div className="chart-tooltip-row">
            <span className="chart-tooltip-star">&#9733;</span> Rating: <strong>{tooltip.rating.toFixed(1)}</strong> / {maxRating}
          </div>
          <div className="chart-tooltip-row">
            Responses: <strong>{tooltip.feedbacks}</strong>
          </div>
        </div>
      )}
      <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} className="trend-line-svg">
        {gridLines.map((v) => {
          const y = padding.top + chartH - ((v - minR) / (maxR - minR)) * chartH;
          return (
            <g key={v}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} className="grid-line" />
              <text x={padding.left - 10} y={y + 4} className="axis-label" textAnchor="end">{v}</text>
            </g>
          );
        })}

        <path d={areaPath} className="trend-area" />
        <path d={linePath} className="trend-line-path" />

        {points.map((p) => (
          <g key={p.week}>
            <circle cx={p.x} cy={p.y} r={5} className="trend-dot" />
            <circle
              cx={p.x} cy={p.y} r={16}
              className="trend-dot-hover"
              onMouseEnter={(e) => handleDotEnter(p, e)}
              onMouseLeave={() => setTooltip(null)}
            />
            <text x={p.x} y={padding.top + chartH + 20} className="axis-label" textAnchor="middle">
              {new Date(p.week).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function Dashboard() {
  const [authenticated, setAuthenticated] = useState(!!sessionStorage.getItem("admin_token"));
  const [data, setData] = useState(null);
  const [feedbacks, setFeedbacks] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [showAll, setShowAll] = useState(false);

  const fetchTrends = useCallback(async (start, end) => {
    try {
      const trends = await getDailyTrends(start || null, end || null);
      setTrendData(trends);
    } catch (err) {
      if (err.status === 401 || err.status === 403) return;
    }
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const [summary, recentFeedbacks, trends] = await Promise.all([
        getDashboardSummary(),
        getRecentFeedbacks(),
        getDailyTrends(null, null),
      ]);
      setData(summary);
      setFeedbacks(recentFeedbacks);
      setTrendData(trends);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      if (err.status === 401 || err.status === 403) {
        sessionStorage.removeItem("admin_token");
        sessionStorage.removeItem("admin_username");
        sessionStorage.removeItem("admin_display_name");
        setAuthenticated(false);
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authenticated) return;
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData, authenticated]);

  if (!authenticated) {
    return <LoginForm onLogin={() => { setAuthenticated(true); setLoading(true); }} />;
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-card card">
        <h2>Failed to load dashboard</h2>
        <p>{error}</p>
        <button className="submit-btn" style={{ maxWidth: 200, margin: "20px auto" }} onClick={fetchData}>
          Retry
        </button>
      </div>
    );
  }

  const maxRating = 5;

  return (
    <div>
      {/* KPI Cards */}
      <div className="metrics-grid">
        <MetricsCard
          title="Overall Rating"
          value={data.overall_avg_rating.toFixed(1)}
          subtitle={`out of ${maxRating}`}
          icon="&#9733;"
        />
        <MetricsCard
          title="Total Feedbacks"
          value={data.total_feedbacks}
          subtitle="responses collected"
          icon="&#128172;"
        />
        <MetricsCard
          title="Total Meetings"
          value={data.total_meetings}
          subtitle="calls tracked"
          icon="&#128197;"
        />
      </div>

      {/* Daily Trend Line Chart */}
      <div className="dashboard-section">
        <div className="trend-header">
          <h2 className="section-title">
            Daily Trend
            {trendData.length >= 2 && (() => {
              const last = trendData[trendData.length - 1].average_rating;
              const prev = trendData[trendData.length - 2].average_rating;
              const diff = last - prev;
              if (diff > 0) return <span className="trend-arrow trend-up"> &#9650; +{diff.toFixed(1)}</span>;
              if (diff < 0) return <span className="trend-arrow trend-down"> &#9660; {diff.toFixed(1)}</span>;
              return <span className="trend-arrow trend-flat"> &#9654; 0.0</span>;
            })()}
          </h2>
          <div className="date-picker-row">
            <input
              type="date"
              className="date-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <span className="date-separator">to</span>
            <input
              type="date"
              className="date-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
            <button
              className="date-apply-btn"
              onClick={() => fetchTrends(startDate, endDate)}
              disabled={!startDate || !endDate}
            >
              Apply
            </button>
            {(startDate || endDate) && (
              <button
                className="date-clear-btn"
                onClick={() => { setStartDate(""); setEndDate(""); fetchTrends("", ""); }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
        <div className="card">
          {trendData.length > 0 ? (
            <TrendLineChart trends={trendData} maxRating={maxRating} />
          ) : (
            <div style={{ textAlign: "center", padding: 40, color: "var(--color-text-muted)" }}>
              No feedback data for the selected date range.
            </div>
          )}
        </div>
      </div>

      {/* Leaderboard */}
      <div className="dashboard-section">
        <h2 className="section-title">Migration Manager Leaderboard</h2>
        <Leaderboard data={data.mm_stats} />
      </div>

      {/* Recent Feedbacks (last 5) */}
      <div className="dashboard-section">
        <h2 className="section-title">Recent Feedbacks</h2>
        {feedbacks.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--color-text-muted)" }}>
            No feedback submissions yet.
          </div>
        ) : (
          <>
            <FeedbackTable items={feedbacks.slice(0, 5)} />
            {feedbacks.length > 5 && !showAll && (
              <div style={{ textAlign: "center", marginTop: 16 }}>
                <button className="view-all-btn" onClick={() => setShowAll(true)}>
                  View All Feedbacks ({feedbacks.length})
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* All Feedbacks (expanded) */}
      {showAll && feedbacks.length > 5 && (
        <div className="dashboard-section">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h2 className="section-title" style={{ marginBottom: 0 }}>All Feedbacks ({feedbacks.length})</h2>
            <button className="date-clear-btn" onClick={() => setShowAll(false)}>Collapse</button>
          </div>
          <FeedbackTable items={feedbacks} />
        </div>
      )}

      {lastUpdated && (
        <p style={{ textAlign: "center", color: "var(--color-text-muted)", fontSize: 12, marginTop: 24 }}>
          Auto-refreshes every 3 minutes &middot; Last updated{" "}
          {lastUpdated.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
