export interface StatItem {
    Name: string;
    Matches: number;
    Wins: number;
    Rate: number;
}


export interface Member {
    Name: string;
    InsightsLink: string;
    LeagueID: string;
    RelicID: string;
    SteamID: string;
    Clan: string;
    ToornamentProfile: string;
    Image: string;
    Elo1v1: number;
    EloTeam: number;
    Ath1v1: number;
    AthTeam: number;
    EloTurn: number;
    FlankRate: number;
    PocketRate: number;
    Civs1v1: Array<StatItem>;
    CivsOp1v1: Array<StatItem>;
    CivsTeam: Array<StatItem>;
    CivsOpTeam: Array<StatItem>;
    Maps1v1: Array<StatItem>;
    MapsTeam: Array<StatItem>;
    TeamMates: Array<StatItem>;
}


export interface Stage {
    id: string;
    number: number;
    name: string;
    type: string;
    status: string;
    closed: boolean;
    groups: Array<Group>;
    table: Map<string, TableRow>;
    nextRound: Array<string>
}


export interface TableRow {
    id: string;
    name: string;
    wins: number;
    losses: number;
    diff: number;
    pts: number;
    rounds: Map<string, TableRowRound>;
}


export interface TableRowRound {
    id: string;
    name: string;
    number: number;
    opponent: string;
    result: Array<number>;
    match: string;
}


export interface Group {
    id: string;
    number: number;
    name: string;
    status: string;
    closed: boolean;
    rounds: Array<Round>;
}


export interface Round {
    id: string;
    number: number;
    name: string;
    status: string;
    closed: boolean;
    matches: Array<Match>;
}


export interface Match {
    id: string;
    number: number;
    status: string;
    opponents: Array<Opponent>;
    playedAt: string;
    civDraft: Draft;
    mapDraft: Draft;
    games: Array<Game>;
    meta: MatchMeta;
}

export interface MatchMeta {
    civs: string;
    maps: string;
}


export interface Draft {
    link: string;
    admin_bans: Array<string>;
    homeBans: Array<string>;
    homePicks: Array<string>;
    homeSnipes: Array<string>;
    awayBans: Array<string>;
    awayPicks: Array<string>;
    awaySnipes: Array<string>;
}


export interface Game {
    insightsLink: string;
    map: string;
    homeCiv: string;
    awayCiv: string;
    winner: string;
}


export interface Opponent {
    id: string;
    number: number;
    position: number;
    result: string;
    forfeit: boolean;
    score: number;
    rank: Object;
    name?: string;
    image?: string;
}


export interface Team {
    Name: string;
    Link: string;
    Logo: string;
    Elo: number;
    Members: Array<Member>;
}


export interface CalendarItem {
    stage: string;
    number: number;
    date:  string;
    time:  string;
    home:  string;
    away:  string;
}