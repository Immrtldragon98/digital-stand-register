export function runtimeHours(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Not recorded";
  const hours = Number(value);
  if (!Number.isFinite(hours) || hours < 0) return "Not recorded";
  return `${hours.toLocaleString("en-IN", {maximumFractionDigits: 1})} h`;
}
export function runtimeLabel(value: unknown, known: unknown, complete: unknown) {
  if (complete === false) return known == null ? "Incomplete history" : `${runtimeHours(known)} measured · partial`;
  return runtimeHours(value);
}
