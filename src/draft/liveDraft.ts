import { io, type Socket } from 'socket.io-client';
import {
    emptyWatched,
    type DraftEvent,
    type DraftState,
    type WatchedDraft,
} from './types';

const AOE2CM = 'https://aoe2cm.net';

function asDraftState(data: Partial<DraftState> | null | undefined): DraftState {
    return {
        nameHost: data?.nameHost ?? '',
        nameGuest: data?.nameGuest ?? '',
        events: Array.isArray(data?.events) ? data.events : [],
        preset: {
            name: data?.preset?.name,
            draftOptions: data?.preset?.draftOptions ?? [],
            turns: data?.preset?.turns ?? [],
        },
    };
}

function isFinished(state: DraftState): boolean {
    const turns = state.preset.turns?.length ?? 0;
    if (turns === 0) return false;
    return state.events.length >= turns;
}

/**
 * Spectate one draft. The id is part of the handshake, so each call opens its
 * own connection. A finished draft arrives as `replay`; a live one stays open
 * and streams `playerEvent` / `adminEvent`. The server disconnects spectators
 * when the draft ends.
 */
export function watchDraft(id: string, onChange: (draft: WatchedDraft) => void): () => void {
    if (!id) {
        onChange(emptyWatched());
        return () => {};
    }

    let disposed = false;
    let current: WatchedDraft = { id, status: 'connecting', state: null, error: null };
    const publish = (draft: WatchedDraft) => {
        current = draft;
        if (!disposed) onChange(draft);
    };
    publish(current);

    const socket: Socket = io(AOE2CM, {
        query: { draftId: id },
        forceNew: true,
        withCredentials: false,
        // Engine.IO polling responses omit CORS headers, so a page on another
        // origin has to open the WebSocket directly.
        transports: ['websocket'],
    });

    const applyState = (state: DraftState, status: WatchedDraft['status']) => {
        publish({ id, status, state, error: null });
    };

    socket.on('draft_state', (data: Partial<DraftState>) => {
        const state = asDraftState(data);
        applyState(state, isFinished(state) ? 'finished' : 'live');
    });

    socket.on('replay', (data: Partial<DraftState>) => {
        applyState(asDraftState(data), 'finished');
    });

    socket.on('playerEvent', (event: DraftEvent) => {
        if (!current.state) return;
        const state = { ...current.state, events: [...current.state.events, event] };
        applyState(state, isFinished(state) ? 'finished' : 'live');
    });

    socket.on('adminEvent', (message: { events?: DraftEvent[] }) => {
        if (!current.state) return;
        const events = Array.isArray(message?.events) ? message.events : current.state.events;
        const state = { ...current.state, events: [...events] };
        applyState(state, isFinished(state) ? 'finished' : 'live');
    });

    socket.on('message', (message: unknown) => {
        if (typeof message === 'string' && message.toLowerCase().includes('does not exist')) {
            publish({ id, status: 'missing', state: null, error: 'This draft does not exist.' });
        }
    });

    socket.on('connect_error', () => {
        if (current.status === 'finished' || current.status === 'missing') return;
        if (current.state) return;
        publish({ id, status: 'error', state: null, error: 'Could not connect to aoe2cm.' });
    });

    socket.on('disconnect', (reason: string) => {
        if (reason !== 'io server disconnect') return;
        if (current.status === 'missing' || !current.state) return;
        publish({ ...current, status: 'finished', error: null });
    });

    return () => {
        disposed = true;
        socket.removeAllListeners();
        socket.disconnect();
    };
}
