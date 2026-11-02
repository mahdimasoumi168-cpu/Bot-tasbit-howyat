import { describe, expect, it } from "vitest";
import { expectedPayerAmount, matchesRialitFee } from "../src/fees.js";

describe("Rialit fee policy", () => {
  it("adds 12 percent on top of the base amount and rounds to 50 toman", () => {
    expect(expectedPayerAmount(100_000, 12)).toBe(112_000);
    expect(expectedPayerAmount(5_600, 12)).toBe(6_272);
  });
  it("requires Rialit's payer amount and fee to match the configured 12 percent", () => {
    expect(matchesRialitFee(100_000, 112_000, 12_000, 12)).toBe(true);
    expect(matchesRialitFee(100_000, 113_650, 13_650, 12)).toBe(false);
    expect(matchesRialitFee(100_000, 112_000, 11_000, 12)).toBe(false);
  });
  it("rejects invalid amounts and percentages", () => {
    expect(() => expectedPayerAmount(0, 12)).toThrow();
    expect(() => expectedPayerAmount(100_000, 100)).toThrow();
  });
});
