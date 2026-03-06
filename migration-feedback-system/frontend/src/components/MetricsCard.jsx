export default function MetricsCard({ title, value, subtitle, icon }) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div className="card-title">{title}</div>
          <div className="card-value">{value}</div>
          {subtitle && (
            <div style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 4 }}>
              {subtitle}
            </div>
          )}
        </div>
        {icon && (
          <span style={{ fontSize: 32, opacity: 0.3 }} dangerouslySetInnerHTML={{ __html: icon }} />
        )}
      </div>
    </div>
  );
}
