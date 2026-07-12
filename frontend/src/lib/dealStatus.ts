export type DealStatus = 'On track' | 'Needs attention' | 'Stalled' | 'Closed';

export function statusColor(status: DealStatus): string {
  switch (status) {
    case 'On track':
      return 'var(--color-green)';
    case 'Needs attention':
      return 'var(--color-amber)';
    case 'Stalled':
      return 'var(--color-red)';
    case 'Closed':
      return 'var(--color-gray)';
  }
}
