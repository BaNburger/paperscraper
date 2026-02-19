import { describe, it, expect } from "vitest";
import { cn, formatDate, truncate, getScoreColor, getScoreBgColor } from "./utils";

describe("cn", () => {
  it("merges class names correctly", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    const includeBar = false;
    const includeBarAlways = true;
    expect(cn("foo", includeBar ? "bar" : null, "baz")).toBe("foo baz");
    expect(cn("foo", includeBarAlways ? "bar" : null, "baz")).toBe("foo bar baz");
  });

  it("merges tailwind classes correctly", () => {
    // twMerge should resolve conflicting classes
    expect(cn("p-4", "p-2")).toBe("p-2");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("handles undefined and null values", () => {
    expect(cn("foo", undefined, "bar")).toBe("foo bar");
    expect(cn("foo", null, "bar")).toBe("foo bar");
  });

  it("handles array of classes", () => {
    expect(cn(["foo", "bar"])).toBe("foo bar");
  });
});

describe("formatDate", () => {
  it("formats date string correctly", () => {
    const result = formatDate("2024-01-15");
    expect(result).toMatch(/Jan 15, 2024/);
  });

  it("formats Date object correctly", () => {
    const date = new Date(2024, 0, 15); // January 15, 2024
    const result = formatDate(date);
    expect(result).toMatch(/Jan 15, 2024/);
  });

  it("handles different months", () => {
    expect(formatDate("2024-06-20")).toMatch(/Jun 20, 2024/);
    expect(formatDate("2024-12-25")).toMatch(/Dec 25, 2024/);
  });
});

describe("truncate", () => {
  it("returns original string if shorter than limit", () => {
    expect(truncate("Hello", 10)).toBe("Hello");
    expect(truncate("Hello", 5)).toBe("Hello");
  });

  it("truncates string and adds ellipsis", () => {
    expect(truncate("Hello World", 5)).toBe("Hello...");
    expect(truncate("This is a long sentence", 10)).toBe("This is a ...");
  });

  it("handles empty string", () => {
    expect(truncate("", 5)).toBe("");
  });

  it("handles exact length", () => {
    expect(truncate("Hello", 5)).toBe("Hello");
  });
});

describe("getScoreColor", () => {
  it("returns green for high scores (>= 8)", () => {
    expect(getScoreColor(8)).toBe("text-green-600");
    expect(getScoreColor(9)).toBe("text-green-600");
    expect(getScoreColor(10)).toBe("text-green-600");
  });

  it("returns yellow for good scores (6-7)", () => {
    expect(getScoreColor(6)).toBe("text-yellow-600");
    expect(getScoreColor(7)).toBe("text-yellow-600");
    expect(getScoreColor(7.9)).toBe("text-yellow-600");
  });

  it("returns orange for moderate scores (4-5)", () => {
    expect(getScoreColor(4)).toBe("text-orange-600");
    expect(getScoreColor(5)).toBe("text-orange-600");
    expect(getScoreColor(5.9)).toBe("text-orange-600");
  });

  it("returns red for low scores (< 4)", () => {
    expect(getScoreColor(0)).toBe("text-red-600");
    expect(getScoreColor(3)).toBe("text-red-600");
    expect(getScoreColor(3.9)).toBe("text-red-600");
  });
});

describe("getScoreBgColor", () => {
  it("returns green background for high scores (>= 8)", () => {
    expect(getScoreBgColor(8)).toBe("bg-green-100");
    expect(getScoreBgColor(10)).toBe("bg-green-100");
  });

  it("returns yellow background for good scores (6-7)", () => {
    expect(getScoreBgColor(6)).toBe("bg-yellow-100");
    expect(getScoreBgColor(7)).toBe("bg-yellow-100");
  });

  it("returns orange background for moderate scores (4-5)", () => {
    expect(getScoreBgColor(4)).toBe("bg-orange-100");
    expect(getScoreBgColor(5)).toBe("bg-orange-100");
  });

  it("returns red background for low scores (< 4)", () => {
    expect(getScoreBgColor(0)).toBe("bg-red-100");
    expect(getScoreBgColor(3)).toBe("bg-red-100");
  });
});
