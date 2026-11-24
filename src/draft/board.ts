import type { DraftOption, DraftState } from './types';

export type Side = 'HOST' | 'GUEST' | 'NONE';

export interface BoardPick {
    id: string;
    optionId: string;
    name: string;
    imageUrl: string;
    picker: Side;
    hidden: boolean;
    snipe?: boolean;
}

const HIDDEN_IDS = new Set([
    'HIDDEN_PICK',
    'HIDDEN_BAN',
    'HIDDEN_SNIPE',
    'HIDDEN_STEAL',
    'HIDDEN',
    'RANDOM',
]);

const AOE2CM = 'https://aoe2cm.net';

function chosenId(event: { chosenOptionId?: string; civilisation?: { name?: string } }): string {
    if (event.chosenOptionId) return event.chosenOptionId;
    return event.civilisation?.name ?? '';
}

function isHidden(id: string): boolean {
    return !id || HIDDEN_IDS.has(id);
}

function absolute(url: string | undefined): string {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    if (url.startsWith('/')) return `${AOE2CM}${url}`;
    return url;
}

function mapFallback(optionId: string): string {
    const file = optionId.replaceAll(' ', '_');
    return `https://files.aoe2germany.de/files/maps-draft/1v1_10_${file}.png`;
}

function imageFor(kind: 'map' | 'civ', optionId: string, option: DraftOption | undefined): string {
    if (kind === 'map') {
        return absolute(option?.imageUrls?.unit || option?.imageUrls?.emblem) || mapFallback(optionId);
    }
    return absolute(option?.imageUrls?.emblem)
        || `${AOE2CM}/images/civemblems/${optionId.toLowerCase()}.png`;
}

function sideOf(player: string | undefined): Side | null {
    if (player === 'HOST' || player === 'GUEST' || player === 'NONE') return player;
    return null;
}

function collect(state: DraftState, kind: 'map' | 'civ', action: 'pick' | 'ban'): BoardPick[] {
    const options = new Map((state.preset.draftOptions ?? []).map((option) => [option.id, option]));
    const snipes: string[] = [];
    if (action === 'pick') {
        for (const event of state.events) {
            if (event.actionType !== 'snipe') continue;
            const id = chosenId(event);
            if (!isHidden(id)) snipes.push(id);
        }
    }

    const picks: BoardPick[] = [];
    state.events.forEach((event, index) => {
        if (event.actionType !== action) return;
        const picker = sideOf(event.player);
        if (!picker) return;
        if (kind === 'civ' && action === 'pick' && picker === 'NONE') return;

        const optionId = chosenId(event);
        const hidden = isHidden(optionId);
        if (!hidden) {
            const snipeAt = snipes.indexOf(optionId);
            if (snipeAt >= 0) {
                snipes.splice(snipeAt, 1);
                return;
            }
        }

        const option = options.get(optionId);
        picks.push({
            id: `e${index}`,
            optionId,
            name: hidden ? 'Hidden' : (option?.name || optionId),
            imageUrl: hidden ? '' : imageFor(kind, optionId, option),
            picker,
            hidden,
        });
    });

    if (kind === 'map') {
        return [
            ...picks.filter((pick) => pick.picker === 'NONE'),
            ...picks.filter((pick) => pick.picker !== 'NONE'),
        ];
    }
    return picks;
}

export function pickedMaps(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    return collect(state, 'map', 'pick');
}

export function pickedCivs(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    return collect(state, 'civ', 'pick');
}

export function bannedCivs(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    return collect(state, 'civ', 'ban');
}

export function bannedMaps(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    return collect(state, 'map', 'ban');
}

export function snipedMaps(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    const options = new Map((state.preset.draftOptions ?? []).map((option) => [option.id, option]));
    const snipes: BoardPick[] = [];
    state.events.forEach((event, index) => {
        if (event.actionType !== 'snipe') return;
        const picker = sideOf(event.player);
        if (!picker) return;
        const optionId = chosenId(event);
        const hidden = isHidden(optionId);
        const option = options.get(optionId);
        snipes.push({
            id: `e${index}`,
            optionId,
            name: hidden ? 'Hidden' : (option?.name || optionId),
            imageUrl: hidden ? '' : imageFor('map', optionId, option),
            picker,
            hidden,
            snipe: true,
        });
    });
    return snipes;
}

export type WinnerSide = 'HOST' | 'GUEST';

export function guessTeamSize(names: (string | undefined)[]): number {
    for (const name of names) {
        const match = name?.match(/\b([1-4])\s*v\s*\1\b/i);
        if (match) return Number(match[1]);
    }
    return 1;
}

export function parsePlacement(value: string): { mapId: string; slot: number } {
    const at = value.lastIndexOf('@');
    if (at === -1) return { mapId: value, slot: 0 };
    const slot = Number(value.slice(at + 1));
    if (!Number.isInteger(slot) || slot < 0) return { mapId: value, slot: 0 };
    return { mapId: value.slice(0, at), slot };
}

export function formatPlacement(mapId: string, slot: number): string {
    return slot === 0 ? mapId : `${mapId}@${slot}`;
}

export interface BoardSave {
    placements: Record<string, string>;
    winners: Record<string, WinnerSide>;
    teamSize?: number;
}

export function boardKey(mapId: string, civId: string): string {
    return `draft-board:${mapId}:${civId}`;
}

function emptySave(): BoardSave {
    return { placements: {}, winners: {} };
}

function asStringRecord(value: unknown): Record<string, string> {
    if (!value || typeof value !== 'object') return {};
    const record: Record<string, string> = {};
    for (const [key, item] of Object.entries(value)) {
        if (typeof item === 'string') record[key] = item;
    }
    return record;
}

function teamSizeOf(value: unknown): { teamSize: number } | Record<string, never> {
    if (value === 1 || value === 2 || value === 3 || value === 4) return { teamSize: value };
    return {};
}

export function readBoard(key: string): BoardSave {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return emptySave();
        const parsed = JSON.parse(raw) as unknown;
        if (!parsed || typeof parsed !== 'object') return emptySave();
        const record = parsed as Record<string, unknown>;
        if (record.placements && typeof record.placements === 'object') {
            const winners: Record<string, WinnerSide> = {};
            if (record.winners && typeof record.winners === 'object') {
                for (const [mapId, side] of Object.entries(record.winners)) {
                    if (side === 'HOST' || side === 'GUEST') winners[mapId] = side;
                }
            }
            return {
                placements: asStringRecord(record.placements),
                winners,
                ...teamSizeOf(record.teamSize),
            };
        }
        return { placements: asStringRecord(parsed), winners: {} };
    } catch {
        return emptySave();
    }
}

export function writeBoard(key: string, save: BoardSave) {
    if (!key) return;
    localStorage.setItem(key, JSON.stringify(save));
}

export function prunePlacements(
    placements: Record<string, string>,
    mapIds: Set<string>,
    civIds: Set<string>,
    teamSize = 4,
): Record<string, string> {
    let changed = false;
    const next: Record<string, string> = {};
    for (const [civId, raw] of Object.entries(placements)) {
        const { mapId, slot } = parsePlacement(raw);
        if (civIds.has(civId) && mapIds.has(mapId) && slot < teamSize) next[civId] = raw;
        else changed = true;
    }
    return changed ? next : placements;
}

export function pruneWinners(
    winners: Record<string, WinnerSide>,
    mapIds: Set<string>,
): Record<string, WinnerSide> {
    let changed = false;
    const next: Record<string, WinnerSide> = {};
    for (const [mapId, side] of Object.entries(winners)) {
        if (mapIds.has(mapId)) next[mapId] = side;
        else changed = true;
    }
    return changed ? next : winners;
}
