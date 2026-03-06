import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { adminSignup } from "../api/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", display_name: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const data = await adminSignup(form.username, form.display_name, form.password);
      sessionStorage.setItem("admin_token", data.token);
      sessionStorage.setItem("admin_username", data.username);
      sessionStorage.setItem("admin_display_name", data.display_name);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Signup failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="feedback-container">
      <form className="feedback-card" onSubmit={handleSubmit}>
        <h2>Create Account</h2>
        <p style={{ marginBottom: 24 }}>Sign up to access the dashboard</p>

        {error && <p style={{ color: "var(--color-danger)", marginBottom: 16 }}>{error}</p>}

        <input
          type="text"
          name="display_name"
          placeholder="Full Name"
          value={form.display_name}
          onChange={handleChange}
          className="comment-box"
          style={{ minHeight: "auto", marginBottom: 12 }}
          required
        />
        <input
          type="text"
          name="username"
          placeholder="Username"
          value={form.username}
          onChange={handleChange}
          className="comment-box"
          style={{ minHeight: "auto", marginBottom: 12 }}
          required
          minLength={3}
        />
        <input
          type="password"
          name="password"
          placeholder="Password (min 6 characters)"
          value={form.password}
          onChange={handleChange}
          className="comment-box"
          style={{ minHeight: "auto", marginBottom: 20 }}
          required
          minLength={6}
        />

        <button type="submit" className="submit-btn" disabled={submitting}>
          {submitting ? "Creating Account..." : "Sign Up"}
        </button>

        <p style={{ marginTop: 16, fontSize: 14, color: "var(--color-text-muted)" }}>
          Already have an account?{" "}
          <Link to="/dashboard" style={{ color: "var(--color-primary)", textDecoration: "none", fontWeight: 600 }}>
            Sign In
          </Link>
        </p>
      </form>
    </div>
  );
}
