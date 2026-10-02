import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatLatency(latencyMs: number | null | undefined): string {
  if (latencyMs == null) return "--";
  if (latencyMs < 1000) return `${Math.round(latencyMs)}ms`;
  return `${(latencyMs / 1000).toFixed(2)}s`;
}

export function formatPercent(val: number | null | undefined): string {
  if (val == null) return "--";
  return `${Math.round(val * 100)}%`;
}
