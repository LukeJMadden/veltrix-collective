import { clsx, type ClassValue } from 'clsx';
import { formatDistanceToNow, format } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatRelativeTime(dateString: string): string {
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  } catch {
    return '';
  }
}

export function formatDate(dateString: string): string {
  try {
    return format(new Date(dateString), 'MMM d, yyyy');
  } catch {
    return '';
  }
}

export function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.substring(0, length).trim() + '...';
}

export function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    'claude-tools': 'Claude Tools',
    'llm': 'LLMs',
    'image': 'Image Gen',
    'video': 'Video',
    'audio': 'Audio',
    'coding': 'Coding',
    'writing': 'Writing',
    'productivity': 'Productivity',
    'voice': 'Voice',
  };
  return labels[category] || category;
}

export function getProviderColor(provider: string): string {
  const colors: Record<string, string> = {
    anthropic: '#cc785c',
    openai: '#10a37f',
    google: '#4285f4',
    meta: '#0866ff',
    mistral: '#ff7000',
  };
  return colors[provider] || '#8b9ab0';
}

export function formatCost(cost: number): string {
  if (cost === 0) return 'Free';
  if (cost < 1) return `$${cost.toFixed(2)}`;
  return `$${cost.toFixed(2)}`;
}

export function formatContextWindow(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(0)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(0)}K`;
  return tokens.toString();
}
