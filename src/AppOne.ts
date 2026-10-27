import type { Member, StatItem, Stage, Match, TableRow, TableRowRound, CalendarItem} from './types'


export interface Pairing {
    player1: TableRow;
    player2: TableRow;
    table: number;
}

export type ScoreOverride = [number, number]; // [opponent0 games, opponent1 games]

export interface PreliminaryStats {
    wins: number;
    losses: number;
    diff: number;
    pts: number;
}

/** Cycle from clicking player's view: 2:0 → 1:1 → 0:2 → clear. Stored in Match.opponents order. */
export function cycleOverrideFromPlayerView(
    current: ScoreOverride | undefined,
    playerIsOpponent0: boolean,
): ScoreOverride | undefined {
    const sequence: ScoreOverride[] = [[2, 0], [1, 1], [0, 2]];

    const currentFromPlayer: ScoreOverride | undefined = current === undefined
        ? undefined
        : playerIsOpponent0 ? current : [current[1], current[0]];

    let nextIdx = 0;
    if (currentFromPlayer !== undefined) {
        const idx = sequence.findIndex(
            ([a, b]) => a === currentFromPlayer[0] && b === currentFromPlayer[1],
        );
        nextIdx = idx + 1;
        if (nextIdx >= sequence.length) {
            return undefined; // clear
        }
    }

    const nextFromPlayer = sequence[nextIdx];
    return playerIsOpponent0
        ? nextFromPlayer
        : [nextFromPlayer[1], nextFromPlayer[0]];
}

function isPendingResult(result: Array<number>): boolean {
    return result[0] === 0 && result[1] === 0;
}

function resultForPlayer(
    pid: string,
    matchId: string,
    official: Array<number>,
    overrides: Map<string, ScoreOverride>,
    matchesById: Map<string, Match>,
): [number, number] {
    const override = overrides.get(matchId);
    if (override === undefined) {
        return [official[0], official[1]];
    }
    const match = matchesById.get(matchId);
    if (match === undefined) {
        return [official[0], official[1]];
    }
    if (match.opponents[0].id === pid) {
        return [override[0], override[1]];
    }
    return [override[1], override[0]];
}

/**
 * Recompute standings applying provisional score overrides.
 * Override values are in Match.opponents order: [o0 games, o1 games].
 */
export function recomputePreliminaryTable(
    table: Map<string, TableRow>,
    overrides: Map<string, ScoreOverride>,
    matchesById: Map<string, Match>,
): Array<[string, PreliminaryStats]> {
    // Pass 1: provisional wins/losses per player
    const provisional = new Map<string, {
        wins: number;
        losses: number;
        results: Map<string, [number, number]>; // opponentId -> result from this player's view
    }>();

    for (const [pid, row] of table) {
        let wins = 0;
        let losses = 0;
        const results = new Map<string, [number, number]>();

        for (const [, rnd] of row.rounds) {
            const result = resultForPlayer(pid, rnd.match, rnd.result, overrides, matchesById);
            results.set(rnd.opponent, result);
            wins += result[0];
            losses += result[1];
        }

        provisional.set(pid, { wins, losses, results });
    }

    // Pass 2: Buchholz = sum of opponents' provisional wins, skipping pending 0:0
    const stats = new Map<string, PreliminaryStats>();
    for (const [pid, p] of provisional) {
        let pts = 0;
        for (const [oppId, result] of p.results) {
            if (isPendingResult(result)) continue;
            pts += provisional.get(oppId)?.wins ?? 0;
        }
        stats.set(pid, {
            wins: p.wins,
            losses: p.losses,
            diff: p.wins - p.losses,
            pts,
        });
    }

    return [...stats].sort((entryA, entryB) => {
        const [aid, a] = entryA;
        const [bid, b] = entryB;
        if (b.wins !== a.wins) return b.wins - a.wins;
        if (b.pts !== a.pts) return b.pts - a.pts;
        return aid.localeCompare(bid);
    });
}

function playedAgainst(player1: TableRow, opponent: string) {
    for ( const [id, round] of player1.rounds ) {
        if ( round.opponent === opponent ) {
            return true
        }
    }
    return false;
}

export function generateNextRound(stage : Stage | undefined) {
    if ( !stage ) {
        return;
    }

    const players = stage.table
    if ( players.size <= 1 ) {
        return;
    }

    // Sort once: primary = points desc, secondary = tiebreak desc, tertiary = id (stable)
    const sorted = [...players].sort((entryA, entryB) => {
        const [aid, a] = entryA;
        const [bid, b] = entryB;
        a.id = aid;
        b.id = bid;
        if ( b.wins !== a.wins) return b.wins - a.wins;
        if ( b.pts !== a.pts) return b.pts - a.pts;
        return aid.localeCompare(bid);
    });

    const used = new Set<string>();
    const pairings: Pairing[] = [];
    let table = 1;

    // Group by exact points
    const groups = new Map<number, TableRow[]>();
    for ( const [pid, p] of sorted ) {
        if ( !groups.has(p.wins)) groups.set(p.wins, []);
        groups.get(p.wins)!.push(p);
    }

    const scoreBrackets = Array.from(groups.keys()).sort((a, b) => b - a);

    // Try to pair within each score bracket (high vs low)
    for ( const points of scoreBrackets ) {
        let bracket = groups.get(points)!.filter(p => !used.has(p.id));

        while (bracket.length >= 2) {
            // Always take current highest remaining
            const high = bracket[0];
            if ( used.has(high.id) ) {
                bracket = bracket.filter(p => p.id !== high.id);
                continue;
            }

            // Find lowest player that high hasn't played
            let low: TableRow | undefined;
            for ( let i = bracket.length - 1; i >= 0; i-- ) {
                const candidate = bracket[i];
                if ( !used.has(candidate.id) && !playedAgainst(high, candidate.id) ) {
                    low = candidate;
                    break;
                }
            }

            if ( !low ) break; // can't pair high → leave for downfloat

            // Pair them!
            used.add(high.id);
            used.add(low.id);
            pairings.push({
                player1: high,
                player2: low,
                table: table++,
            });

            // Remove both from bracket
            bracket = bracket.filter(p => p.id !== high.id && p.id !== low.id);
        }
    }

    // Remaining unpaired players (downfloats + odd ones)
    const remaining = sorted.filter((entry) => !used.has(entry[0]));

  // Pair remaining across brackets (still high vs low)
    let i = 0;
    while ( i < remaining.length - 1 ) {
        const [p1id, p1] = remaining[i];
        let paired = false;

        for (let j = i + 1; j < remaining.length; j++) {
            const [p2id, p2] = remaining[j];
            if ( !playedAgainst(p1, p2id) ) {
                pairings.push({ player1: p1, player2: p2, table: table++ });
                remaining.splice(j, 1);
                paired = true;
                break;
            }
        }

        if ( paired ) {
            remaining.splice(i, 1);
        } else {
            i++; // can't pair this one yet, skip and come back
        }
    }

    // Last player gets bye (prefer one who hasn't had one)
    if (remaining.length === 1) {
        console.log("One player remaining")
        console.log(pairings)
        const byePlayer = remaining[0];
        // return [...pairings, { player: byePlayer, table: table }];
    }
    console.log(pairings)
    let nextRound: string[] = [];
    for ( const [pid, row] of stage.table ) {
        const pair = pairings.find(pair => pair.player1.id === pid || pair.player2.id === pid)
        if ( pair === undefined ) {
            continue
        }
        nextRound.push(pair.player1.id === pid ? pair.player2.id : pair.player1.id);
    }
    stage.nextRound=nextRound;

}