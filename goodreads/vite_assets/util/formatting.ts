export function formatNumber(number: number | bigint): string {
  return new Intl.NumberFormat("en-US").format(number);
}
