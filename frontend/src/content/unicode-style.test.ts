import { describe, expect, it } from "vitest";
import { toUnicodeBold, toUnicodeItalic } from "./unicode-style";

describe("toUnicodeBold", () => {
  it("maps letters and digits to bold codepoints", () => {
    expect(toUnicodeBold("Ab1")).toBe("𝐀𝐛𝟏");
  });

  it("leaves punctuation and spaces untouched", () => {
    expect(toUnicodeBold("Hi, world!")).toBe("𝐇𝐢, 𝐰𝐨𝐫𝐥𝐝!");
  });
});

describe("toUnicodeItalic", () => {
  it("maps letters to italic codepoints", () => {
    expect(toUnicodeItalic("Ab")).toBe("𝐴𝑏");
  });

  it("uses the Planck-constant exception for lowercase h", () => {
    expect(toUnicodeItalic("h")).toBe("ℎ");
  });

  it("leaves digits untouched (no italic digit block exists)", () => {
    expect(toUnicodeItalic("123")).toBe("123");
  });
});
