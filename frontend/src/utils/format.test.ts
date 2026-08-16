import { describe, expect, it } from "vitest";
import { classificationTone, confidenceTone, formatCompact, formatCurrency, formatR2, formatRoi } from "./format";

describe("formatCurrency", () => {
  it("formats billions, millions, thousands and small values", () => {
    expect(formatCurrency(2_700_000_000)).toBe("$2.70B");
    expect(formatCurrency(123_456_789)).toBe("$123.5M");
    expect(formatCurrency(4_500)).toBe("$4.5K");
    expect(formatCurrency(42)).toBe("$42");
  });

  it("handles null/undefined/NaN", () => {
    expect(formatCurrency(null)).toBe("—");
    expect(formatCurrency(undefined)).toBe("—");
    expect(formatCurrency(Number.NaN)).toBe("—");
  });
});

describe("formatCompact", () => {
  it("abbreviates large numbers", () => {
    expect(formatCompact(1_000_000_000)).toBe("1.00B");
    expect(formatCompact(2_500_000)).toBe("2.5M");
    expect(formatCompact(900)).toBe("900");
  });
});

describe("formatR2 / formatRoi", () => {
  it("formats scores", () => {
    expect(formatR2(0.6529)).toBe("0.6529");
    expect(formatRoi(3.2)).toBe("3.20x");
  });
});

describe("confidenceTone", () => {
  it("maps confidence to tone buckets", () => {
    expect(confidenceTone(80)).toBe("high");
    expect(confidenceTone(60)).toBe("medium");
    expect(confidenceTone(30)).toBe("low");
  });
});

describe("classificationTone", () => {
  it("returns a css class for every known category", () => {
    expect(classificationTone("BLOCKBUSTER")).toContain("emerald");
    expect(classificationTone("SUPER_HIT")).toContain("emerald");
    expect(classificationTone("HIT")).toContain("cyan");
    expect(classificationTone("AVERAGE")).toContain("amber");
    expect(classificationTone("FLOP")).toContain("rose");
  });
});
