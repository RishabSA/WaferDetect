import { describe, expect, it } from "vitest";

import { dollars, percent, png } from "./format";

describe("format", () => {
  it("formats dollars without cents", () => {
    expect(dollars(12422.31)).toBe("$12,422");
  });

  it("formats fractions as percentages", () => {
    expect(percent(0.9103)).toBe("91.0%");
  });

  it("prefixes base64 as a data url", () => {
    expect(png("abc123")).toBe("data:image/png;base64,abc123");
  });
});
