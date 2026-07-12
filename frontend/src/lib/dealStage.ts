import type { StageSegment } from '../components/StageDiagram';

export const STAGE_NAMES = [
  'Lead',
  'NDA',
  'Sourcing & Screening',
  'Valuation & Bidding',
  'Strategy & Preparation',
  'Due Diligence',
  'Negotiation & Closing',
] as const;

function daysSince(isoDate: string): number {
  const ms = Date.now() - new Date(isoDate).getTime();
  return Math.max(0, Math.floor(ms / (1000 * 60 * 60 * 24)));
}

/**
 * Builds the 7-segment stepper from a deal's current stage name.
 * Only the current segment gets a day count — the schema tracks
 * `stage_entered_at` for the current stage only, not a full per-stage
 * transition history (system-architecture.md Section 3.1).
 */
export function buildStageSegments(currentStage: string, stageEnteredAt?: string): StageSegment[] {
  const currentIndex = STAGE_NAMES.indexOf(currentStage as (typeof STAGE_NAMES)[number]);
  return STAGE_NAMES.map((name, i) => ({
    name,
    status: i < currentIndex ? 'done' : i === currentIndex ? 'current' : 'future',
    days: i === currentIndex && stageEnteredAt ? daysSince(stageEnteredAt) : undefined,
  }));
}
