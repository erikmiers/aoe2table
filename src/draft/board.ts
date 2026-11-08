import type { DraftOption, DraftState } from './types';

export type Side = 'HOST' | 'GUEST' | 'NONE';

export interface BoardPick {
    id: string;
    optionId: string;
    name: string;
    imageUrl: string;
    picker: Side;
    hidden: boolean;
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

function collect(state: DraftState, kind: 'map' | 'civ'): BoardPick[] {
    const options = new Map((state.preset.draftOptions ?? []).map((option) => [option.id, option]));
    const snipes: string[] = [];
    for (const event of state.events) {
        if (event.actionType !== 'snipe') continue;
        const id = chosenId(event);
        if (!isHidden(id)) snipes.push(id);
    }

    const picks: BoardPick[] = [];
    state.events.forEach((event, index) => {
        if (event.actionType !== 'pick') return;
        const picker = sideOf(event.player);
        if (!picker) return;
        if (kind === 'civ' && picker === 'NONE') return;

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
    return collect(state, 'map');
}

export function pickedCivs(state: DraftState | null): BoardPick[] {
    if (!state) return [];
    return collect(state, 'civ');
}

export function boardKey(mapId: string, civId: string): string {
    return `draft-board:${mapId}:${civId}`;
}

export function readPlacements(key: string): Record<string, string> {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return {};
        const parsed = JSON.parse(raw) as unknown;
        if (!parsed || typeof parsed !== 'object') return {};
        const placements: Record<string, string> = {};
        for (const [civId, mapId] of Object.entries(parsed)) {
            if (typeof mapId === 'string') placements[civId] = mapId;
        }
        return placements;
    } catch {
        return {};
    }
}

export function writePlacements(key: string, placements: Record<string, string>) {
    if (!key) return;
    localStorage.setItem(key, JSON.stringify(placements));
}

export function prunePlacements(
    placements: Record<string, string>,
    mapIds: Set<string>,
    civIds: Set<string>,
): Record<string, string> {
    let changed = false;
    const next: Record<string, string> = {};
    for (const [civId, mapId] of Object.entries(placements)) {
        if (civIds.has(civId) && mapIds.has(mapId)) next[civId] = mapId;
        else changed = true;
    }
    return changed ? next : placements;
}
