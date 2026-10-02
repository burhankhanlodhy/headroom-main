export function cn(...inputs: Array<string | false | null | undefined>): string {
  return inputs.filter(Boolean).join(" ");
}

const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const full = new Intl.NumberFormat("en");

export function fmtCompact(n: number): string {
  return compact.format(n);
}

export function fmtFull(n: number): string {
  return full.format(n);
}

export function fmtUsd(n: number): string {
  if (n >= 1000) return `$${compact.format(n)}`;
  // Whole dollars stay short ($5); any cents show both digits ($2.50).
  const cents = Number.isInteger(Math.round(n * 100) / 100) ? 0 : 2;
  return `$${n.toLocaleString("en", { minimumFractionDigits: cents, maximumFractionDigits: 2 })}`;
}

/** Deterministic pseudo-random from a string seed — keeps mock charts stable across reloads. */
export function seeded(seed: string): () => number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return () => {
    h ^= h << 13;
    h ^= h >>> 17;
    h ^= h << 5;
    return ((h >>> 0) % 10000) / 10000;
  };
}

export function lastDays(n: number): string[] {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(Date.now() - (n - 1 - i) * 86_400_000);
    return d.toISOString().slice(0, 10);
  });
}

export function dayLabel(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("en", { month: "short", day: "numeric" });
}
