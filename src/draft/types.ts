export interface DraftOption {
    id: string;
    name?: string;
    imageUrls?: {
        unit?: string;
        emblem?: string;
        animated_left?: string;
        animated_right?: string;
    };
}

export interface DraftTurn {
    player: string;
    action: string;
}

export interface DraftEvent {
    player?: string;
    executingPlayer?: string;
    actionType?: string;
    action?: string;
    chosenOptionId?: string;
    civilisation?: { name?: string };
}

export interface DraftState {
    nameHost: string;
    nameGuest: string;
    events: DraftEvent[];
    preset: {
        name?: string;
        draftOptions?: DraftOption[];
        turns?: DraftTurn[];
    };
}

export type DraftStatus = 'idle' | 'connecting' | 'live' | 'finished' | 'missing' | 'error';

export interface WatchedDraft {
    id: string;
    status: DraftStatus;
    state: DraftState | null;
    error: string | null;
}

export function emptyWatched(): WatchedDraft {
    return { id: '', status: 'idle', state: null, error: null };
}

/** Public ids are 5 letters. Private ids are an underscore plus 5 letters. */
const DRAFT_ID = /^_?[A-Za-z]{5}$/;

export function parseDraftId(raw: string): string {
    const trimmed = raw.trim();
    if (!trimmed) return '';
    if (DRAFT_ID.test(trimmed)) return trimmed;

    const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    try {
        const url = new URL(withProtocol);
        const parts = url.pathname.split('/').filter(Boolean);
        const markerAt = parts.findIndex((part) => {
            const name = part.toLowerCase();
            return name === 'draft' || name === 'spectate';
        });
        const candidate = markerAt >= 0 ? parts[markerAt + 1] : undefined;
        if (candidate && DRAFT_ID.test(candidate)) return candidate;
    } catch {
        // Not a URL. Fall through to the path fragment below.
    }

    const fromPath = trimmed.match(/\/(?:draft|spectate)\/(_?[A-Za-z]{5})\b/i);
    return fromPath?.[1] ?? '';
}
