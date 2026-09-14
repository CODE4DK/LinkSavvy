import { describe, expect, it } from "vitest";
import { addDays, eachDay, monthGridRange, toISODate, weekRange } from "./calendar-dates";

describe("toISODate", () => {
  it("formats a date as YYYY-MM-DD", () => {
    expect(toISODate(new Date(2026, 5, 3))).toBe("2026-06-03");
  });
});

describe("monthGridRange", () => {
  it("starts on the Monday on/before the 1st and ends on the Sunday on/after the last day", () => {
    const { start, end } = monthGridRange(new Date(2026, 5, 15));
    expect(start.getDay()).toBe(1);
    expect(end.getDay()).toBe(0);
    expect(toISODate(start) <= "2026-06-01").toBe(true);
    expect(toISODate(end) >= "2026-06-30").toBe(true);
  });
});

describe("weekRange", () => {
  it("returns the Monday-to-Sunday week containing the anchor", () => {
    const { start, end } = weekRange(new Date(2026, 5, 17));
    expect(start.getDay()).toBe(1);
    expect(end.getDay()).toBe(0);
    expect(eachDay(start, end)).toHaveLength(7);
  });
});

describe("addDays", () => {
  it("advances by the given number of days", () => {
    expect(toISODate(addDays(new Date(2026, 5, 30), 2))).toBe("2026-07-02");
  });
});
