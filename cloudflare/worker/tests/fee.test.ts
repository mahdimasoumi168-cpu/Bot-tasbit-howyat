import { describe, expect, it } from "vitest";
import { expectedPayerAmount } from "../src/fees.js";

describe("Rialit payer fee calculation", () => {
  it("matches Rialit's 12% gross-up example and rounds up to 50 toman", () => {
    expect(expectedPayerAmount(100_000, 12)).toBe(113_650);
  });
  it("keeps the merchant's base amount separate from payer fee", () => {
    const base = 250_000;
    expect(expectedPayerAmount(base, 12)).toBeGreaterThan(base);
    expect(base).toBe(250_000);
  });
  it("rejects invalid fee percentages", () => {
    expect(() => expectedPayerAmount(100_000, 100)).toThrow();
  });
});
