/**
 * Tool marks for the launcher cards.
 *
 * Claude Code and OpenCode use their marks from Simple Icons
 * (https://simpleicons.org, CC0; the trademarks remain their owners'), shown
 * unaltered to identify the tool. OpenAI's logo is not used for Codex: it is
 * not in Simple Icons and OpenAI restricts third-party use, so Codex gets a
 * neutral terminal glyph drawn for this app.
 */

const CLAUDE_CODE =
  "M21 10.5h3v3h-3v3h-1.5v3H18v-3h-1.5v3H15v-3H9v3H7.5v-3H6v3H4.5v-3H3v-3H0v-3h3v-6h18Zm-15 0h1.5v-3H6Zm10.5 0H18v-3h-1.5z";
const OPENCODE = "M22 24H2V0h20zM17 4.8H7v14.4h10z";

export function ToolIcon({ id, name }: { id: string; name: string }) {
  if (id === "claude") {
    return (
      <span className="tool-icon" title={name}>
        <svg viewBox="0 0 24 24" role="img" aria-label={name}>
          <path d={CLAUDE_CODE} fill="#D97757" />
        </svg>
      </span>
    );
  }
  if (id === "opencode") {
    return (
      <span className="tool-icon" title={name}>
        <svg viewBox="0 0 24 24" role="img" aria-label={name}>
          <path d={OPENCODE} fill="currentColor" fillRule="evenodd" />
        </svg>
      </span>
    );
  }
  if (id === "codex") {
    return (
      <span className="tool-icon" title={name}>
        <svg viewBox="0 0 24 24" role="img" aria-label={name}>
          <rect x="1.5" y="3" width="21" height="18" rx="4" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path d="M6.5 9l3.5 3-3.5 3" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12.5 15.5h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </span>
    );
  }
  return <span className="mark small-mark">{name.slice(0, 1)}</span>;
}
