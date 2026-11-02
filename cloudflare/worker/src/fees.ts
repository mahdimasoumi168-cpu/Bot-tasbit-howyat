export function expectedPayerAmount(baseToman: number, feePercent = 12): number {
  if (!Number.isSafeInteger(baseToman) || baseToman < 1) throw new Error("invalid_base_amount");
  if (!Number.isFinite(feePercent) || feePercent < 0 || feePercent >= 100) throw new Error("invalid_fee_percent");
  return Math.ceil(baseToman * (1 + feePercent / 100));
}

export function matchesRialitFee(baseToman: number, payerAmount: number, payerFee: number, feePercent = 12): boolean {
  const expected = expectedPayerAmount(baseToman, feePercent);
  return Number.isSafeInteger(payerAmount) && Number.isSafeInteger(payerFee) &&
    payerAmount === expected && payerFee === expected - baseToman;
}
