export function expectedPayerAmount(baseToman: number, feePercent = 12): number {
  if (!Number.isSafeInteger(baseToman) || baseToman < 1) throw new Error("invalid_base_amount");
  if (!Number.isFinite(feePercent) || feePercent < 0 || feePercent >= 100) throw new Error("invalid_fee_percent");
  if (feePercent === 0) return baseToman;
  return Math.ceil((baseToman * 100 / (100 - feePercent)) / 50) * 50;
}
