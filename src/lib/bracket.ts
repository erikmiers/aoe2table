import type { Stage, Match, Opponent } from '../types';

export interface BracketSlot {
    playerId?: string;
    score?: number | null;
    isBye?: boolean;
    seed?: number;
}

export interface BracketMatch {
    id?: string;
    status: string;
    label?: string;
    slots: [BracketSlot, BracketSlot];
    match?: Match;
}

export interface BracketRound {
    name: string;
    matches: BracketMatch[];
}

export interface Bracket {
    spots: number;
    rounds: BracketRound[];
    thirdPlace?: BracketMatch;
    isPreview: boolean;
}

/** Swiss stages are 1–5; matching Finals are number + 5. */
export function getPairedFinalsStage(stages: Stage[], swiss: Stage): Stage | undefined {
    return stages.find(
        (s) => s.type === 'single_elimination' && s.number === swiss.number + 5,
    ) ?? stages.find(
        (s) => s.type === 'single_elimination' && s.name.startsWith(swiss.name.replace(/\s*Liga\s*$/i, '').trim()),
    );
}

export function getPairedSwissStage(stages: Stage[], finals: Stage): Stage | undefined {
    return stages.find(
        (s) => s.type === 'swiss' && s.number === finals.number - 5,
    ) ?? stages.find(
        (s) => s.type === 'swiss' && finals.name.startsWith(s.name.replace(/\s*Liga\s*$/i, '').trim()),
    );
}

export function getSwissLeagues(stages: Stage[]): Stage[] {
    return stages.filter((s) => s.type === 'swiss').sort((a, b) => a.number - b.number);
}

function stageHasMatches(stage: Stage): boolean {
    return (stage.groups ?? []).some((g) =>
        (g.rounds ?? []).some((r) => (r.matches ?? []).length > 0),
    );
}

function slotFromOpponent(op: Opponent | undefined): BracketSlot {
    if (!op || !op.id) {
        return { isBye: true };
    }
    return {
        playerId: op.id,
        score: op.score ?? null,
    };
}

function matchToBracketMatch(match: Match, label?: string): BracketMatch {
    const o0 = match.opponents?.[0];
    const o1 = match.opponents?.[1];
    return {
        id: match.id,
        status: match.status ?? 'pending',
        label,
        slots: [slotFromOpponent(o0), slotFromOpponent(o1)],
        match,
    };
}

/** Split final round matches into championship final vs 3rd-place when both exist. */
function splitFinalRound(matches: Match[]): { final?: BracketMatch; thirdPlace?: BracketMatch } {
    if (matches.length === 0) return {};
    if (matches.length === 1) {
        return { final: matchToBracketMatch(matches[0], 'Finale') };
    }
    // Heuristic: higher match number or second entry is often final; keep stable by number
    const sorted = [...matches].sort((a, b) => a.number - b.number);
    return {
        thirdPlace: matchToBracketMatch(sorted[0], 'Platz 3'),
        final: matchToBracketMatch(sorted[sorted.length - 1], 'Finale'),
    };
}

/**
 * Build a bracket from real Toornament matches on a Finals stage.
 * Returns undefined if the stage has no matches yet.
 */
export function buildBracketFromStage(finals: Stage, spots: number): Bracket | undefined {
    if (!stageHasMatches(finals)) {
        return undefined;
    }

    const group = finals.groups[0];
    const rounds = [...(group?.rounds ?? [])].sort((a, b) => a.number - b.number);
    const bracketRounds: BracketRound[] = [];
    let thirdPlace: BracketMatch | undefined;

    for (let i = 0; i < rounds.length; i++) {
        const round = rounds[i];
        const matches = [...(round.matches ?? [])].sort((a, b) => a.number - b.number);
        const isLast = i === rounds.length - 1;

        if (isLast) {
            const split = splitFinalRound(matches);
            thirdPlace = split.thirdPlace;
            if (split.final) {
                bracketRounds.push({ name: 'Finale', matches: [split.final] });
            }
            continue;
        }

        bracketRounds.push({
            name: round.name,
            matches: matches.map((m) => matchToBracketMatch(m)),
        });
    }

    // 6-player: ensure QF shows bye rows for seeds 1–2 if only 2 QF matches
    if (spots === 6 && bracketRounds[0] && bracketRounds[0].matches.length === 2) {
        // Leave as-is; fixture path adds explicit bye cards. Real data may only list played QFs.
    }

    return {
        spots,
        rounds: bracketRounds,
        thirdPlace,
        isPreview: false,
    };
}
