import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { validateToken, submitFeedback } from "../api/api";

const EXPERIENCE_LABELS = [
  "Extremely dissatisfied",
  "Dissatisfied",
  "Neutral",
  "Satisfied",
  "Extremely satisfied",
];

const CONFIDENCE_OPTIONS = [
  "Not Confident",
  "Slightly Confident",
  "Moderately Confident",
  "Confident",
  "Very Confident",
];

const REQUIREMENT_OPTIONS = ["Yes", "No", "Partially"];

const CONCERN_OPTIONS = [
  "Yes, fully resolved",
  "Partially resolved",
  "Not resolved",
];

function RatingScale({ value, onChange, labels }) {
  return (
    <div className="cf-rating-scale">
      <div className="cf-rating-labels">
        <span>{labels[0]}</span>
        <span>{labels[labels.length - 1]}</span>
      </div>
      <div className="cf-rating-dots">
        {labels.map((label, i) => {
          const val = i + 1;
          return (
            <button
              key={val}
              type="button"
              className={`cf-rating-dot ${value === val ? "active" : ""}`}
              onClick={() => onChange(val)}
              title={label}
            >
              {val}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function RadioGroup({ options, value, onChange, name }) {
  return (
    <div className="cf-radio-group">
      {options.map((opt) => (
        <label key={opt} className={`cf-radio-label ${value === opt ? "active" : ""}`}>
          <input
            type="radio"
            name={name}
            value={opt}
            checked={value === opt}
            onChange={() => onChange(opt)}
          />
          <span className="cf-radio-circle" />
          <span className="cf-radio-text">{opt}</span>
        </label>
      ))}
    </div>
  );
}

export default function FeedbackPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const presetRating = parseInt(searchParams.get("rating"), 10) || 0;

  const [state, setState] = useState("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const [context, setContext] = useState(null);

  const [overallRating, setOverallRating] = useState(presetRating);
  const [businessRequirement, setBusinessRequirement] = useState("");
  const [confidenceLevel, setConfidenceLevel] = useState("");
  const [engineerRating, setEngineerRating] = useState(0);
  const [improvements, setImprovements] = useState("");
  const [concernResolved, setConcernResolved] = useState("");

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

  const isValid =
    overallRating >= 1 &&
    businessRequirement &&
    confidenceLevel &&
    engineerRating >= 1 &&
    improvements.trim();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isValid) return;

    setState("submitting");
    try {
      await submitFeedback({
        token,
        rating: overallRating,
        business_requirement: businessRequirement,
        confidence_level: confidenceLevel,
        engineer_rating: engineerRating,
        improvements,
        concern_resolved: concernResolved || null,
      });
      setState("success");
    } catch (err) {
      setErrorMsg(err.message);
      setState(err.status === 409 ? "already_submitted" : "error");
    }
  }

  if (state === "loading") {
    return (
      <div className="cf-form-wrapper">
        <div className="cf-form-card">
          <div className="cf-form-loading">
            <div className="spinner" style={{ borderTopColor: "#6B2FA0" }} />
            <p>Validating your link...</p>
          </div>
        </div>
      </div>
    );
  }

  if (state === "already_submitted") {
    return (
      <div className="cf-form-wrapper">
        <div className="cf-form-card">
          <div className="cf-form-header" />
          <div className="cf-form-body cf-center">
            <div className="cf-success-icon">&#10003;</div>
            <h2>Already Submitted</h2>
            <p>You've already provided feedback for this meeting. Thank you!</p>
          </div>
        </div>
      </div>
    );
  }

  if (state === "error") {
    return (
      <div className="cf-form-wrapper">
        <div className="cf-form-card">
          <div className="cf-form-header" />
          <div className="cf-form-body cf-center">
            <h2 style={{ color: "#dc2626" }}>Something went wrong</h2>
            <p>{errorMsg}</p>
          </div>
        </div>
      </div>
    );
  }

  if (state === "success") {
    return (
      <div className="cf-form-wrapper">
        <div className="cf-form-card">
          <div className="cf-form-header" />
          <div className="cf-form-body cf-center">
            <div className="cf-success-icon">&#127775;</div>
            <h2 style={{ color: "#16a34a" }}>Thank You!</h2>
            <p>Your feedback has been recorded. We appreciate your time.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cf-form-wrapper">
      <form className="cf-form-card" onSubmit={handleSubmit}>
        <div className="cf-form-header">
          <h1>Migration Feedback Form</h1>
          <p>
            Thank you for participating in today's CloudFuze migration session.
            Your feedback helps us enhance our service and better support your migration needs.
            All information shared will remain confidential.
          </p>
        </div>

        <div className="cf-form-body">
          <p className="cf-required-note"><span className="cf-required">*</span> Required</p>

          {/* Q1 — Overall Experience */}
          <div className="cf-question">
            <label className="cf-question-label">
              How would you rate your overall experience? <span className="cf-required">*</span>
            </label>
            <RatingScale
              value={overallRating}
              onChange={setOverallRating}
              labels={EXPERIENCE_LABELS}
            />
          </div>

          {/* Q2 — Business Requirement */}
          <div className="cf-question">
            <label className="cf-question-label">
              Did we understand your business requirement properly? <span className="cf-required">*</span>
            </label>
            <RadioGroup
              options={REQUIREMENT_OPTIONS}
              value={businessRequirement}
              onChange={setBusinessRequirement}
              name="business_req"
            />
          </div>

          {/* Q3 — Confidence Level */}
          <div className="cf-question">
            <label className="cf-question-label">
              After today's call, how confident do you feel about the progress of your migration project? <span className="cf-required">*</span>
            </label>
            <RadioGroup
              options={CONFIDENCE_OPTIONS}
              value={confidenceLevel}
              onChange={setConfidenceLevel}
              name="confidence"
            />
          </div>

          {/* Q4 — Engineer Rating */}
          <div className="cf-question">
            <label className="cf-question-label">
              How would you rate the clarity and professionalism of our migration engineer during the call? <span className="cf-required">*</span>
            </label>
            <RatingScale
              value={engineerRating}
              onChange={setEngineerRating}
              labels={EXPERIENCE_LABELS}
            />
          </div>

          {/* Q5 — Improvements */}
          <div className="cf-question">
            <label className="cf-question-label">
              Is there anything we could improve or any additional support you require? <span className="cf-required">*</span>
            </label>
            <textarea
              className="cf-textarea"
              placeholder="Enter your answer"
              value={improvements}
              onChange={(e) => setImprovements(e.target.value)}
            />
          </div>

          {/* Q6 — Concern Resolved */}
          <div className="cf-question">
            <label className="cf-question-label">
              Was your concern or query addressed effectively during the call?
            </label>
            <RadioGroup
              options={CONCERN_OPTIONS}
              value={concernResolved}
              onChange={setConcernResolved}
              name="concern"
            />
          </div>

          <button
            type="submit"
            className="cf-submit-btn"
            disabled={!isValid || state === "submitting"}
          >
            {state === "submitting" ? "Submitting..." : "Submit"}
          </button>
        </div>
      </form>

      <div className="cf-form-footer">
        <p>CloudFuze Migration Team &bull; This link is unique to you.</p>
      </div>
    </div>
  );
}
