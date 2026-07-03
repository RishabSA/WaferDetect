export const dollars = (value: number): string =>
  value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });

export const percent = (value: number): string => `${(value * 100).toFixed(1)}%`;

export const png = (base64: string): string => `data:image/png;base64,${base64}`;
