import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import StarRating from "../components/StarRating";
import { validateToken, submitFeedback } from "../api/api";

export default function FeedbackPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const presetRating = parseInt(searchParams.get("rating"), 10) || 0;

  const [state, setState] = useState("loading"); // loading | ready | submitting | success | error
  const [errorMsg, setErrorMsg] = useState("");
  const [context, setContext] = useState(null);
  const [rating, setRating] = useState(presetRating);
  const [comment, setComment] = useState("");

  useEffect(() => {
    if (!token) {
      setErrorMsg("No feedback token provided. Please use the link from your email.");
      setState("error");
      return;
    }

    validateToken(token)
      .then((data) => {
        setContext(data);
        setState("ready");
      })
      .catch((err) => {
        setErrorMsg(err.message);
        setState(err.status === 409 ? "already_submitted" : "error");
      });
  }, [token]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (rating < 1) return;

    setState("submitting");
    try {
      await submitFeedback({ token, rating, comment: comment || null });
      setState("success");
    } catch (err) {
      setErrorMsg(err.message);
      setState(err.status === 409 ? "already_submitted" : "error");
    }
  }

  if (state === "loading") {
    return (
      <div className="feedback-container">
        <div className="feedback-card loading">
          <div className="spinner" />
          <p>Validating your link...</p>
        </div>
      </div>
    );
  }

  if (state === "already_submitted") {
    return (
      <div className="feedback-container">
        <div className="feedback-card success-card">
          <div className="success-icon">&#10003;</div>
          <h2>Already Submitted</h2>
          <p>You've already provided feedback for this meeting. Thank you!</p>
        </div>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="feedback-container">
        <div className="feedback-card error-card">
          <h2>Something went wrong</h2>
          <p>{errorMsg}</p>
        </div>
      </div>
    );
  }

  if (state === "success") {
    return (
      <div className="feedback-container">
        <div className="feedback-card success-card">
          <div className="success-icon">&#127775;</div>
          <h2>Thank You!</h2>
          <p>Your feedback has been recorded. We appreciate your time.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-container">
      <form className="feedback-card" onSubmit={handleSubmit}>
        <h2>Rate Your Experience</h2>
        <p>
          How was your migration call?
          {context?.customer_email && (
            <span style={{ display: "block", fontSize: 13, marginTop: 4 }}>
              {context.customer_email}
            </span>
          )}
        </p>

        <StarRating value={rating} onChange={setRating} />

        <textarea
          className="comment-box"
          placeholder="Any additional comments? (optional)"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />

        <button
          type="submit"
          className="submit-btn"
          disabled={rating < 1 || state === "submitting"}
        >
          {state === "submitting" ? "Submitting..." : "Submit Feedback"}
        </button>
      </form>
    </div>
  );
}
