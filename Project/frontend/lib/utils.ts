import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatLiters(liters: number): string {
  if (liters >= 1000000) return `${(liters / 1000000).toFixed(2)} ML`;
  if (liters >= 1000) return `${(liters / 1000).toFixed(1)} KL`;
  return `${liters.toFixed(0)} L`;
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
}

export const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

export const ROOF_TYPE_LABELS: Record<string, string> = {
  RCC: 'RCC Concrete',
  METAL: 'Metal/GI Sheet',
  TILE: 'Clay/Mangalore Tile',
  GREEN: 'Green Roof',
  ASPHALT: 'Asphalt/Bitumen',
};

export const SOIL_TYPE_LABELS: Record<string, string> = {
  SANDY: 'Sandy (High permeability)',
  LOAMY: 'Loamy (Moderate permeability)',
  CLAY: 'Clay (Low permeability)',
  GRAVELLY: 'Gravelly (Very high permeability)',
  SILTY: 'Silty (Moderate-low permeability)',
};
