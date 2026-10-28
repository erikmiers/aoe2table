import type { Stage, TableRow } from '../types';
import type { Bracket, BracketMatch, BracketRound, BracketSlot } from './bracket';

/** Sorted player ids from a Swiss table (wins → Buchholz → id). */
export function topPlayersFromSwissTable(table: Map<string, TableRow>, n: number): string[] {
    const sorted = [...table.entries()].sort((entryA, entryB) => {
        const [aid, a] = entryA;
        const [bid, b] = entryB;
        if (b.wins !== a.wins) return b.wins - a.wins;
        if (b.pts !== a.pts) return b.pts - a.pts;
        return aid.localeCompare(bid);
    });
    return sorted.slice(0, n).map(([pid]) => pid);
}

function pendingMatch(
    slots: [BracketSlot, BracketSlot],
    label?: string,
): BracketMatch {
    return {
        status: 'pending',
        label,
        slots,
    };
}

function seedSlot(playerId: string | undefined, seed: number): BracketSlot {
    return { playerId, seed };
}

function byeAdvance(playerId: string | undefined, seed: number): BracketMatch {
    return {
        status: 'pending',
        label: 'Bye',
        slots: [
            { playerId, seed, isBye: false },
            { isBye: true, seed: undefined },
        ],
    };
}

/**
 * Synthesize a preview bracket from Swiss standings seeds.
 * 8: classic QF 1v8, 4v5, 2v7, 3v6 → SF → Final + Platz 3
 * 6: QF 3v6, 4v5; seeds 1–2 bye into SF
 */
export function buildFixtureBracket(swiss: Stage, spots: number): Bracket {
    const seeds: Array<string | undefined> = topPlayersFromSwissTable(swiss.table ?? new Map(), spots);
    while (seeds.length < spots) {
        seeds.push(undefined);
    }

    const rounds: BracketRound[] = [];

    if (spots >= 8) {
        // QF pairings: 1v8, 4v5, 2v7, 3v6
        const qf: BracketMatch[] = [
            pendingMatch([seedSlot(seeds[0], 1), seedSlot(seeds[7], 8)]),
            pendingMatch([seedSlot(seeds[3], 4), seedSlot(seeds[4], 5)]),
            pendingMatch([seedSlot(seeds[1], 2), seedSlot(seeds[6], 7)]),
            pendingMatch([seedSlot(seeds[2], 3), seedSlot(seeds[5], 6)]),
        ];
        rounds.push({ name: 'Viertelfinale', matches: qf });

        const sf: BracketMatch[] = [
            pendingMatch([{ seed: 1 }, { seed: 4 }], 'Halbfinale'),
            pendingMatch([{ seed: 2 }, { seed: 3 }], 'Halbfinale'),
        ];
        // Fill SF with TBD placeholders (winners unknown)
        sf[0].slots = [{ }, { }];
        sf[1].slots = [{ }, { }];
        rounds.push({ name: 'Halbfinale', matches: sf });
    } else {
        // 6-player: bye cards for 1 & 2, QF for 3v6 and 4v5
        const qf: BracketMatch[] = [
            byeAdvance(seeds[0], 1),
            pendingMatch([seedSlot(seeds[3], 4), seedSlot(seeds[4], 5)]),
            byeAdvance(seeds[1], 2),
            pendingMatch([seedSlot(seeds[2], 3), seedSlot(seeds[5], 6)]),
        ];
        rounds.push({ name: 'Viertelfinale', matches: qf });

        const sf: BracketMatch[] = [
            pendingMatch([seedSlot(seeds[0], 1), { }], 'Halbfinale'),
            pendingMatch([seedSlot(seeds[1], 2), { }], 'Halbfinale'),
        ];
        rounds.push({ name: 'Halbfinale', matches: sf });
    }

    rounds.push({
        name: 'Finale',
        matches: [pendingMatch([{ }, { }], 'Finale')],
    });

    const thirdPlace = pendingMatch([{ }, { }], 'Platz 3');

    return {
        spots,
        rounds,
        thirdPlace,
        isPreview: true,
    };
}

export function resolveBracket(
    finals: Stage,
    swiss: Stage | undefined,
    spots: number,
    buildFromStage: (finals: Stage, spots: number) => Bracket | undefined,
): Bracket {
    const real = buildFromStage(finals, spots);
    if (real) {
        return real;
    }
    if (swiss) {
        return buildFixtureBracket(swiss, spots);
    }
    // Empty shell
    return {
        spots,
        rounds: [
            { name: 'Viertelfinale', matches: [] },
            { name: 'Halbfinale', matches: [] },
            { name: 'Finale', matches: [] },
        ],
        isPreview: true,
    };
}
