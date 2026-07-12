import { buildStageSegments } from '../lib/dealStage';
import type { DealCardData } from '../components/DealCard';

/**
 * Hardcoded demo data for the Phase 1 "Deal card + Kanban" checkpoint only.
 * Replaced by real /deals API data once the backend + seed script exist
 * (phase1-006-wire-dashboard).
 */
export const mockDeals: DealCardData[] = [
  {
    id: 'deal-a',
    name: 'Deal A',
    client: 'Khun A',
    owner: 'PS',
    riskFlags: 3,
    status: 'On track',
    segments: buildStageSegments(5, [9, 14, 21, 18, 26, 11]),
  },
  {
    id: 'deal-b',
    name: 'Horizon Freight Corp',
    client: 'Somsak L.',
    owner: 'DA',
    riskFlags: 1,
    status: 'Needs attention',
    segments: buildStageSegments(2, [12, 19, 24]),
  },
  {
    id: 'deal-c',
    name: 'Nova Fintech',
    client: 'Ariya P.',
    owner: 'MK',
    riskFlags: 0,
    status: 'On track',
    segments: buildStageSegments(6, [7, 10, 15, 20, 22, 30, 6]),
  },
  {
    id: 'deal-d',
    name: 'Atlas Materials',
    client: 'R. Boonmee',
    owner: 'PS',
    riskFlags: 2,
    status: 'Stalled',
    segments: buildStageSegments(1, [16, 41]),
  },
  {
    id: 'deal-e',
    name: 'Bluewave Retail',
    client: 'K. Traikul',
    owner: 'DA',
    riskFlags: 1,
    status: 'On track',
    segments: buildStageSegments(3, [8, 11, 17, 5]),
  },
  {
    id: 'deal-f',
    name: 'Circuit Semiconductors',
    client: 'W. Chatterjee',
    owner: 'MK',
    riskFlags: 0,
    status: 'On track',
    segments: buildStageSegments(0, [3]),
  },
];
