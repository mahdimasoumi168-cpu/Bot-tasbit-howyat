import { describe, expect, it } from "vitest";

function expectedPayerAmount(baseToman: number, feePercent = 12): number {
  return Math.ceil((baseToman * 100 / (100 - feePercent)) / 50) * 50;
}

describe("Rialit payer fee display", () => {
  it("uses the provider's gross-up formula and rounds to 50 toman", () => {
    expect(expectedPayerAmount(100_000, 12)).toBe(113_650);
  });

  it("does not add the fee to the stored base order amount", () => {
    const base = 250_000;
    expect(expectedPayerAmount(base, 12)).toBeGreaterThan(base);
    expect(base).toBe(250_000);
  });
});
