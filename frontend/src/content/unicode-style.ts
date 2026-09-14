/**
 * LinkedIn has no native bold or italics for post text -- these
 * helpers fake it by substituting Unicode "Mathematical Alphanumeric
 * Symbols" that merely *look* bold or italic. They are a different
 * character than the letter they replace, not a style applied to it.
 * A screen reader either can't recognize them as letters at all or
 * reads them out strangely (e.g. spelling them or naming the symbol),
 * so text using these is materially less accessible -- warn the user
 * every time this is offered, never apply it silently.
 */

const UPPER_A = 65;
const UPPER_Z = 90;
const LOWER_A = 97;
const LOWER_Z = 122;
const DIGIT_0 = 48;
const DIGIT_9 = 57;

function mapLetters(
  text: string,
  { upperBase, lowerBase, digitBase }: { upperBase: number; lowerBase: number; digitBase?: number },
): string {
  return Array.from(text)
    .map((ch) => {
      const code = ch.codePointAt(0);
      if (code === undefined) return ch;
      if (code >= UPPER_A && code <= UPPER_Z)
        return String.fromCodePoint(upperBase + (code - UPPER_A));
      if (code >= LOWER_A && code <= LOWER_Z)
        return String.fromCodePoint(lowerBase + (code - LOWER_A));
      if (digitBase !== undefined && code >= DIGIT_0 && code <= DIGIT_9) {
        return String.fromCodePoint(digitBase + (code - DIGIT_0));
      }
      return ch;
    })
    .join("");
}

export function toUnicodeBold(text: string): string {
  return mapLetters(text, { upperBase: 0x1d400, lowerBase: 0x1d41a, digitBase: 0x1d7ce });
}

export function toUnicodeItalic(text: string): string {
  // The math-italic block has no dedicated digits, and skips lowercase
  // "h" (its slot is unassigned) in favour of the pre-existing
  // Planck-constant character -- handled as a one-off exception below.
  return Array.from(text)
    .map((ch) => (ch === "h" ? "ℎ" : mapLetters(ch, { upperBase: 0x1d434, lowerBase: 0x1d44e })))
    .join("");
}
