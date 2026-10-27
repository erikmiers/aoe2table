import type { DraftAnalysis, CompanionRmStats } from '../types';
export const draftCache = new Map<string, DraftAnalysis[]>();
export const statsCache = new Map<string, CompanionRmStats>();