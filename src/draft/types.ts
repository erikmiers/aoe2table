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
const DRAFT_ID = /_?[A-Za-z]{5}/;

export function parseDraftId(raw: string): string {
    const trimmed = raw.trim();
    if (!trimmed) return '';
    const fromPath = trimmed.match(new RegExp(`/draft/(${DRAFT_ID.source})\\b`, 'i'));
    if (fromPath) return fromPath[1];
    if (new RegExp(`^${DRAFT_ID.source}$`).test(trimmed)) return trimmed;
    return '';
}
