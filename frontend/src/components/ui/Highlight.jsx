/** Renders `text` with case-insensitive matches of any `terms` wrapped in <mark>. */
export default function Highlight({ text = "", terms = [] }) {
  if (!text || !terms?.length) return <>{text}</>;
  const escaped = terms.filter(Boolean).map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (!escaped.length) return <>{text}</>;

  // One capture group => String.split places matched separators at odd indices.
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? <mark key={i} className="hl">{part}</mark> : <span key={i}>{part}</span>
      )}
    </>
  );
}
