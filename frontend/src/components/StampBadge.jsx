const STYLES = {
  verified: { color: "var(--verified)", bg: "var(--verified-bg)" },
  flagged: { color: "var(--flagged)", bg: "var(--flagged-bg)" },
  amber: { color: "var(--amber)", bg: "var(--amber-bg)" },
  neutral: { color: "var(--slate)", bg: "#ECEAE1" },
};

export default function StampBadge({ label, tone = "neutral", tilt = -4 }) {
  const s = STYLES[tone] || STYLES.neutral;
  return (
    <span
      className="mono stamp-badge"
      style={{
        color: s.color, borderColor: s.color, background: s.bg,
        transform: `rotate(${tilt}deg)`,
      }}
    >
      {label}
    </span>
  );
}