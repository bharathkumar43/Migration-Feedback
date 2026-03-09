export default function Leaderboard({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--color-text-muted)" }}>
        No feedback data yet. Leaderboard will appear after the first responses.
      </div>
    );
  }

  const sorted = [...data].sort((a, b) => b.average_rating - a.average_rating);

  function renderStars(rating) {
    const full = Math.round(rating);
    return (
      <span className="rating-stars">
        {"\u2605".repeat(full)}
        {"\u2606".repeat(5 - full)}
      </span>
    );
  }

  function rankClass(idx) {
    if (idx === 0) return "rank-badge rank-1";
    if (idx === 1) return "rank-badge rank-2";
    if (idx === 2) return "rank-badge rank-3";
    return "rank-badge";
  }

  return (
    <table className="leaderboard-table">
      <thead>
        <tr>
          <th style={{ width: 60 }}>Rank</th>
          <th>Migration Manager</th>
          <th>Avg Rating</th>
          <th>Feedbacks</th>
          <th>Meetings</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((mm, idx) => (
          <tr key={mm.mm_email}>
            <td>
              <span className={rankClass(idx)}>{idx + 1}</span>
            </td>
            <td style={{ fontWeight: 500 }}>{mm.mm_email}</td>
            <td>
              {renderStars(mm.average_rating)}{" "}
              <span style={{ marginLeft: 8, fontWeight: 600 }}>{mm.average_rating.toFixed(1)}</span>
            </td>
            <td>{mm.total_feedbacks}</td>
            <td>{mm.total_meetings}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
