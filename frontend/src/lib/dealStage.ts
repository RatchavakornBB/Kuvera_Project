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

export function buildStageSegments(currentIndex: number, stageDays?: number[]): StageSegment[] {
  return STAGE_NAMES.map((name, i) => ({
    name,
    status: i < currentIndex ? 'done' : i === currentIndex ? 'current' : 'future',
    days: i <= currentIndex ? stageDays?.[i] : undefined,
  }));
}
