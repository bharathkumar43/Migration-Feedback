import { useState } from "react";

export default function StarRating({ value, onChange, count = 5 }) {
  const [hovered, setHovered] = useState(0);

  return (
    <div className="star-rating-container" onMouseLeave={() => setHovered(0)}>
      {Array.from({ length: count }, (_, i) => {
        const star = i + 1;
        const filled = star <= (hovered || value);
        return (
          <button
            key={star}
            type="button"
            className={`star-btn ${filled ? "active" : ""}`}
            onMouseEnter={() => setHovered(star)}
            onClick={() => onChange(star)}
            aria-label={`Rate ${star} star${star > 1 ? "s" : ""}`}
          >
            {filled ? "\u2605" : "\u2606"}
          </button>
        );
      })}
    </div>
  );
}
