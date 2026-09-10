import type { Member, StatItem, Stage, Match, TableRow, TableRowRound, CalendarItem} from './types'


export interface Pairing {
    player1: TableRow;
    player2: TableRow;
    table: number;
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