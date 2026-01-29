import { BundleData } from './types';

export async function loadBundle(): Promise<BundleData> {
  const response = await fetch('/data/bundle.json');
  if (!response.ok) {
    throw new Error('Failed to load bundle data');
  }
  return response.json();
}
