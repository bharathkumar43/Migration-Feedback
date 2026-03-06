import { useState } from "react";
import { Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import FeedbackPage from "./pages/FeedbackPage";
import Dashboard from "./pages/Dashboard";
import SignupPage from "./pages/SignupPage";

function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const displayName = sessionStorage.getItem("admin_display_name") || "Admin";
  const username = sessionStorage.getItem("admin_username") || "";
  const initial = displayName.charAt(0).toUpperCase();

  function handleLogout() {
    sessionStorage.removeItem("admin_token");
    sessionStorage.removeItem("admin_username");
    sessionStorage.removeItem("admin_display_name");
    setOpen(false);
    navigate("/dashboard");
    window.location.reload();
  }

  return (
    <div className="profile-menu-wrapper">
      <button className="profile-btn" onClick={() => setOpen(!open)} title={displayName}>
        {initial}
      </button>
      {open && (
        <>
          <div className="profile-overlay" onClick={() => setOpen(false)} />
          <div className="profile-dropdown">
            <div className="profile-dropdown-header">
              <div className="profile-avatar-lg">{initial}</div>
              <div>
                <div style={{ fontWeight: 600 }}>{displayName}</div>
                <div style={{ fontSize: 12, color: "var(--color-text-muted)" }}>@{username}</div>
              </div>
            </div>
            <div className="profile-dropdown-divider" />
            <button className="profile-dropdown-item logout-item" onClick={handleLogout}>
              Sign Out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function App() {
  const location = useLocation();
  const isFeedbackPage = location.pathname === "/feedback";
  const isAuthPage = location.pathname === "/signup";
  const isDashboard = location.pathname === "/" || location.pathname === "/dashboard";
  const isLoggedIn = !!sessionStorage.getItem("admin_token");

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-inner">
          <h1 className="logo">
            <span className="logo-icon">&#9733;</span> Migration Feedback
          </h1>
          {!isFeedbackPage && !isAuthPage && (
            <nav className="header-nav">
              <Link to="/dashboard" className={isDashboard ? "active" : ""}>
                Dashboard
              </Link>
              {isLoggedIn && <ProfileMenu />}
            </nav>
          )}
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/feedback" element={<FeedbackPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} CloudFuze &mdash; Migration Feedback System</p>
      </footer>
    </div>
  );
}

export default App;
