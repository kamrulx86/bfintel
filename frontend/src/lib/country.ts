export function countryFlag(code: string | null | undefined): string {
  if (!code || code.length !== 2) return "";
  const upper = code.toUpperCase();
  return String.fromCodePoint(...[...upper].map((c) => 0x1f1e6 - 65 + c.charCodeAt(0)));
}
