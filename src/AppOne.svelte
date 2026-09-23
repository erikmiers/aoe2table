<script lang="ts">
  import "./app.css";

  import { Avatar } from '@skeletonlabs/skeleton';
  import { ConicGradient } from '@skeletonlabs/skeleton';
  import { onMount } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { type Member, type StatItem, type Stage, type Match, type MatchMeta, type TableRow, type TableRowRound, type CalendarItem} from './types.d'
  import { generateNextRound } from "./AppOne";

  const BASE_URL = import.meta.env.BASE_URL;
  const DATA_URL = BASE_URL + "A2GS101V1/";
  const DEVELOPING = false;

  let players: Member[] = [];
  let stages: Stage[] = $state([]);
  let calendar: CalendarItem[] = [];
  let openStage : Stage | undefined = $state(undefined);
  let openMatch : Match | undefined = $state(undefined);
  let openMember : Member | undefined = $state(undefined);
  let hoveredMatch : string | undefined = $state(undefined);
  let hoveredMatchId : string | undefined = $state(undefined);
  let hoveredPlayer : string | undefined = $state(undefined);
  let hoveredRow : TableRow | undefined = undefined;

  const stageIcons: string[] = [
    "dark-age.webp",
    "feudal-age.webp",
    "castle-age.webp",
    "imperial-age.webp",
    "post-imp.jpg",]

  const dayNames = ["Sun", "Mon", "Tue", "Wen", "Thu", "Fri", "Sat"]

  let nextRoundEntries = $derived(Object.entries(openStage?.nextRound ?? {}));


  function getMapUrl(name: string): string {
    let url = "https://www.aoe2insights.com/static/images/maps/" + name.replace(" ", "_").toLowerCase() + ".webp"    
    return url;
  }

  function getCivUrl(name: string): string {
    let url = "https://www.aoe2insights.com/static/images/civs/" + name.replace(" ", "_").toLowerCase() + ".webp"    
    return url;
  }


  function toggleMember(lid: string) {
    if ( openMember?.LeagueID === lid ) {
      openMember = undefined
    } else {
      openMember = players.find((player: Member) => player.LeagueID === lid);
      openMatch = undefined
    }
  }

  function toggleMatch(mid: string) {
    if ( openMatch?.id === mid ) {
      openMatch = undefined
    } else {
      const rounds = openStage ? openStage.groups[0].rounds : [];
      for ( const round of rounds ) {
        const match = round.matches.find((match: Match) => match.id === mid);
        if ( match !== undefined ) {
          const o1 = playerLookUp(match.opponents[0].id)
          match.opponents[0].name = o1 ? o1.Name : ""
          match.opponents[0].image = o1 ? o1.Image : ""
          const o2 = playerLookUp(match.opponents[1].id)
          match.opponents[1].name = o2? o2.Name : ""
          match.opponents[1].image = o2 ? o2.Image : ""
          openMatch = match
          openMember = undefined
          return
        }
      }

    }
  }


  function playerLookUp(nid: string): Member | undefined {
    return players.find((player: Member) => player.LeagueID === nid);
  }

  function imageLookUp(nid: string): string {
    const player = players.find((player: Member) => player.LeagueID === nid);
    return player ? player.Image : "PlayerNotFound";
  }

  function nameLookUp(nid: string): string {
    const player = players.find((player: Member) => player.LeagueID === nid);
    return player ? player.Name : "PlayerNotFound";
  }

  function getBgColor(result: Array<number>): string {
    if ( result[0] == 2 ) {
      return "bg-green-500"
    }
    if ( result[1] == 2) {
      return "bg-orange-500"
    }
    if (result[0] == 1) {
      return "bg-yellow-500"
    }
    return "bg-gray-500"
  }

  function findMatchById(matchId: string): Match | undefined {
    return stages
      .flatMap(stage => stage.groups)
      .flatMap(group => group.rounds)
      .flatMap(round => round.matches)
      .find(match => match.id === matchId);
  }


  function formatMatchResult(match: Match | undefined): string {
    if ( match === undefined ) {
      return "0 : 0"
    }

    let tableRowRound: TableRowRound | undefined = undefined
    for ( const stage of stages ) {
      for ( const table of stage.table ) {
        for ( const round of table[1].rounds ) {
          if ( round[1].match === match.id ) {
            tableRowRound = round[1]
            break
          }
        }
      }
    }

    if ( tableRowRound === undefined ) {
      return "0 : 0"
    }

    if ( match.opponents[0].id === tableRowRound.opponent ) {
      return tableRowRound.result[1] + " : " + tableRowRound.result[0]
    }
    
    return tableRowRound.result[0] + " : " + tableRowRound.result[1]
  }


  function formatMatchDate(match: Match | undefined, fullDate: boolean = false): string {
    if ( match !== undefined ) {
      if ( match.status === "completed" ) {
        let date = new Date(match.playedAt)
        return date.toDateString()
      }

      const name1 = nameLookUp(match.opponents[0].id)
      const name2 = nameLookUp(match.opponents[1].id)
      const matchdate1 = calendar.find((date: CalendarItem) => date.home === name1 || date.away === name1)
      const matchdate2 = calendar.find((date: CalendarItem) => date.home === name2 || date.away === name2)
      const matchdate = matchdate1? matchdate1 : matchdate2;
      if ( matchdate ) {
        let date = new Date(matchdate.date)
        if ( fullDate ) {
          return date.toDateString() + " " + matchdate.time
        }

        return dayNames[date.getDay()] + "  " + matchdate.time
      }
    }

    return ""
  }


  function formatResult(rnd: TableRowRound): string {
    if ( rnd.result[0] === 0 && rnd.result[1] === 0 ) {
      const match = findMatchById(rnd.match)
      const matchDate = formatMatchDate(match)
      if ( matchDate !== "" ) {
        return matchDate
      }
    }

    return rnd.result[0] + ":" + rnd.result[1]
  }


  onMount(async () => {
    // Fetch calendar data
    const response3 = await fetch(DATA_URL+'calendar.json');
    calendar = await response3.json();
    // Fetch player data
    const response = await fetch(DATA_URL+'players.json');
    let fetchedData = await response.json();
    players = fetchedData.sort((a: Member, b: Member) => {
      if ( a.Elo1v1 === undefined ) return 1
      if ( b.Elo1v1 === undefined ) return -1
      return b.Elo1v1 - a.Elo1v1
    }) 
    players.forEach((member: Member) => {
      let sorted1v1Maps: StatItem[] = [];
      if ( member.Maps1v1 !== undefined ) {
          sorted1v1Maps = member.Maps1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sorted1v1Civs: StatItem[] = [];
        if ( member.Civs1v1 !== undefined ) {
          sorted1v1Civs = member.Civs1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sorted1v1OpCivs: StatItem[] = [];
        if ( member.CivsOp1v1 !== undefined ) {
          sorted1v1OpCivs = member.CivsOp1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        member.Maps1v1 = sorted1v1Maps;
        member.Civs1v1 = sorted1v1Civs;
        member.CivsOp1v1 = sorted1v1OpCivs;
      });
    // Fetch toornay data
    let response2 = await fetch(DATA_URL+'toornay.json');
    let fetchedData2 = await response2.json();

    // Properly cast json data into internal type structure
    stages = [...Object.values<Stage>(fetchedData2.stages)];
    for ( const stage of stages ) {
      stage.table = new Map<string, TableRow>(Object.entries(stage.table));
      for ( const [pid, row] of stage.table ) {
        row.rounds = new Map<string, TableRowRound>(Object.entries(row.rounds));
      }
    }
    openStage = stages[0]
  });

function hasMapDraft(match: Match) {
  let meta = match.meta
  if ( meta.maps ) {
    return true
  }
  return false
}

function checkActive(pid : string, a: any, b:any) {
  if ( hoveredRow ) {
    for ( let [id, round] of hoveredRow.rounds ) {
      if ( round.opponent === pid ) {
        return true
      }
    }
  }

  return hoveredMatch === pid || hoveredPlayer === pid;
}

function rowEnter(pid: string, row: TableRow|undefined) {
  hoveredPlayer = pid;
  hoveredRow = row;
}

function rowLeave() {
  hoveredPlayer = undefined;
  hoveredRow = undefined;
}
</script>




<main>
    <!-- <img class="h-24 m-auto" src="{BASE_URL}a2glogoliga.png" alt="">
    <h1 class="mb-8">AoE2Germany Liga - Saison 8</h1> -->


    <div class="logo-cloud grid-cols-1 lg:!grid-cols-5 gap-1">
      {#each stages as stage}
      <a class="logo-item" href="#" onclick={(e) => openStage=stage}>
        <img class="h-8" src="{BASE_URL}{stageIcons[stage.number-1]}" alt="">
        <span>{stage.name}</span>
      </a>
      {/each}
    </div>
    <br>

    <h2 class="mb-8 text-2xl">{openStage?.name}</h2>

    <!-- Responsive Container (recommended) -->
<div class="flex gap-6 overflow-x-auto pb-4">
  <div class="min-w-max">
    <table class="table table-interactive table-hover">
      <thead>
        <tr>
          <th>#</th>
          <th>Name</th>
          <th>Wins</th>
          <th>Losses</th>
          <th>Diff</th>
          <th>Bhlz</th>
          {#if openStage !== undefined}
              {#each openStage.table.values().next().value?.rounds as [rid, rnd], n}
                <th>Round {n+1}</th>
              {/each}
          {/if}
          </tr>
      </thead>
      <tbody>
        {#if openStage !== undefined}
        {#each openStage.table as [pid, row], i}
          {@const activeRow= checkActive(pid, hoveredMatch, hoveredPlayer)}
          <tr>
            <td class:activeRow><span class="font-bold">{i+1}</span></td>
            <td class:activeRow
              class="hover:bg-sky-700 hover:bg-opacity-20" 
              onclick={(e) => toggleMember(pid)}
              onmouseenter={() => rowEnter(pid, row)}
              onmouseleave={() => rowLeave()}>
              <div class="ms-2 flex items-center space-x-2">
                <Avatar width="w-6" initials="{nameLookUp(pid)}" src={imageLookUp(pid)}/>
                <span>{nameLookUp(pid)}</span>
              </div>
            </td>
            <td class:activeRow><span class="font-bold">{row.wins}</span></td>
            <td class:activeRow>{row.losses}</td>
            <td class:activeRow>{row.diff}</td>
            <td class:activeRow><span class="font-bold">{row.pts}</span></td>
            {#each row.rounds as [rid, rnd]}
              <td onclick={() => toggleMatch(rnd.match)}
                  onmouseenter={() => {hoveredMatch = rnd.opponent; hoveredMatchId = rnd.match}}
                  onmouseleave={() => {hoveredMatch = undefined; hoveredMatchId = undefined}}
                  class="{openMatch?.id === rnd.match? 'border border-gray-300':''}
                         {hoveredMatchId === rnd.match? 'border border-yellow-300':''}">
                <div
                  class:bg-opacity-80={hoveredMatch === rnd.opponent || hoveredPlayer === rnd.opponent || hoveredMatchId === rnd.match} 
                  class="w-auto h-10 bg-opacity-30 text-s hover:bg-opacity-50 {getBgColor(rnd.result)}" style="font-size: smaller;">
                  {nameLookUp(rnd.opponent)}<br>
                  <span class="text-surface-400">{formatResult(rnd)}</span>
                  <!-- <span class:text-surface-400={rnd.result[0] === 0 && rnd.result[1] === 0} >{formatResult(rnd)}</span> -->
                </div>
              </td>
            {/each}
          </tr>
        {/each}
        {/if}
      </tbody>
    </table>
  </div>
  {#if DEVELOPING }
  <div class="min-w-max">
    <table class="table table-interactive table-hover">
      <thead>
        <tr><th>
          Next Round
            <span 
              onclick={(e) => generateNextRound(openStage)}
              class="xs-4 cursor-pointer font-bold">&#x21bb;</span>
        </th></tr>
      </thead>
      <tbody>
        <!-- {#if openStage !== undefined && openStage.nextRound !== undefined} -->
        {#each nextRoundEntries as [i, pid] }
          <tr>
            <td
              onclick={(e) => toggleMember(pid)}
              class="hover:bg-sky-700 hover:bg-opacity-20">
              <div class="ms-2 flex items-center space-x-2 h-10">
                <Avatar width="w-6" initials="{nameLookUp(pid)}" src={imageLookUp(pid)}/>
                <span>{nameLookUp(pid)}</span>
              </div>
            </td>
          </tr>
        {/each}
        <!-- {/if} -->
      </tbody>
    </table>
  </div>
  {/if}
</div>

{#if openMatch !== undefined}

 <!-- Member header ---------------------------------------------------->
 <section class="mb-4 mt-8 small-p rounded-lg border border-surface-500 bg-surface-900/50">
  <section class="flex items-center justify-between w-full p-0">
    <div class="flex items-center space-x-4">
      <Avatar width="w-12" src={openMatch.opponents[0].image} initials={openMatch.opponents[0].name}/>
      <span class="text-l">{openMatch.opponents[0].name}</span>
    </div>
    <div class="flex justify-end">
      <div class="flex flex-col items-center">
        <span>{formatMatchResult(openMatch)}</span>
        <small>{formatMatchDate(openMatch, true)}</small>
      </div>
    </div>
    <div class="flex items-center space-x-4">
      <span class="text-l">{openMatch.opponents[1].name}</span>
      <Avatar width="w-12" src={openMatch.opponents[1].image} initials={openMatch.opponents[1].name}/>
    </div>
  </section>
  <section class="flex items-center justify-between w-full p-0 mt-6">
    <div class="flex items-center justify-end m-auto">
      {#if hasMapDraft(openMatch)}
        <a href="https://aoe2cm.net/draft/{openMatch.meta.maps}" target="_blank"
        class="btn btn-sm variant-ghost-primary ms-2 me-auto" data-sveltekit-preload-data="hover">Map Draft</a>
      {/if}
      {#if openMatch.meta.civs}
        <a href="https://aoe2cm.net/draft/{openMatch.meta.civs}" target="_blank"
        class="btn btn-sm variant-ghost-primary ms-2 me-auto" data-sveltekit-preload-data="hover">Civ Draft</a>
      {/if}
    </div>
  </section>
 

  </section>

{/if}

{#if openMember !== undefined}

 <!-- Member header ---------------------------------------------------->
 <section class="mb-4 mt-8 small-p rounded-lg border border-surface-500 bg-surface-900/50">
  <section class="flex items-center justify-between w-full p-0">
    <div class="flex items-center space-x-4">
      <Avatar width="w-12" src={openMember.Image} initials={openMember.Name}/>
      <span class="text-l">{openMember.Name}</span>
    </div>
    
    
    <!-- <a href="https://play.toornament.com/de/tournaments/8544694639084077056/participants/{player.ID}" target="_blank"
    class="btn variant-ghost-surface" data-sveltekit-preload-data="hover">Toornament</a> -->
    <div class="flex items-center justify-end">
      <a href="{openMember.InsightsLink}" target="_blank"
      class="btn btn-sm variant-ghost-primary ms-2 me-auto" data-sveltekit-preload-data="hover">Insights</a>
      {#if openMember.RelicID}
        <a href="https://aoe2.gg/profile/{openMember.RelicID}" target="_blank"
        class="btn btn-sm variant-ghost-primary ms-2 me-auto" data-sveltekit-preload-data="hover">aoe2.gg</a>
        <a href="https://www.aoe2companion.com/players/{openMember.RelicID}" target="_blank"
        class="btn btn-sm variant-ghost-primary ms-2 me-auto" data-sveltekit-preload-data="hover">companion</a>
      {/if}
      <a href="https://play.toornament.com/de/tournaments/8544694639084077056/participants/{openMember.LeagueID}" target="_blank"
      class="btn-icon btn-sm variant-ghost-primary ms-2 me-auto p-2" data-sveltekit-preload-data="hover">
        <img src="https://play.toornament.com/media/7603294581977661440/original" alt="">
      </a>

      <span class="badge variant-ghost-surface me-2 ms-2">1v1</span>
      <div class="card small-p items-center">
        <span class="text-m">{openMember.Elo1v1}</span>
        <span class="text-m text-primary-100/50">&nbsp;{openMember.Ath1v1}</span>
      </div>
        <span class="badge variant-ghost-surface me-2 ms-2">Team</span>
        <div class="card small-p items-center">
          <span class="text-m">{openMember.EloTeam}</span>
          <span class="text-m text-primary-100/50">&nbsp;{openMember.AthTeam}</span>
        </div>
        <!-- <button type="button" class="btn-icon variant-ghost m-4 font-medium text-2xl"
         on:click={() => toggleMembers(player.Name)}> {openMembers.includes(player.Name)?"-":"+"}</button> -->
    </div>
  </section>

  <!-- 1v1 maps and civs ------------------------------------------------>
  <section class="flex items-center justify-between w-full p-2 mt-2 bg-surface-900/60 rounded-lg"
  transition:slide={{ duration: 300 }}
  >
    <span class="gradient-heading">
        1v1 Maps
    </span>
    {#each openMember.Maps1v1.slice(0, 7) as map}
    <div class="justify-center p-1 rounded-lg">
      <span class="text-sm">{map.Name}</span>
      <div class="flex items-center relative rounded-lg border border-surface-500">
        <img class="h-14 me-2" src="{getMapUrl(map.Name)}" alt="">
        <ConicGradient width="w-12" stops=
        {[{color:'rgba(0,255,0,.17)',start:0,end:map.Rate},
              {color:'rgba(255,0,0,.17)',start:map.Rate,end:100}]}>
        </ConicGradient>
        <div class="absolute inset-y-1/2 inset-x-1/4">
          <span class="badge variant-soft-surface">{map.Matches}</span>
        </div>
      </div>
    </div>
    {/each}
  </section>

  <section class="flex items-center w-full p-2 mb-2 bg-surface-900/60 rounded-lg"
  transition:slide={{ duration: 300 }}
  >
    <span class="gradient-heading">
        1v1 Civs
    </span>

    <div class="snap-x scroll-px-4 snap-mandatory scroll-smooth overflow-x-auto">
      <div class="flex items-center justify-between w-full">
        {#each openMember.Civs1v1.slice(0, 20) as civ}
        <div class="justify-center p-1 rounded-lg">
          <span class="text-sm text-primary-100/50">{civ.Name}</span>
          <div class="flex items-center justify-between p-1 rounded-lg bg-surface-900 w-28">
            <img class="h-6 me-2" src="{getCivUrl(civ.Name)}" alt="">
            <span class="badge variant-soft-surface">{civ.Matches}</span>
            <ConicGradient width="w-6 ms-2" stops=
            {[{color:'rgba(0,255,0,.17)',start:0,end:civ.Rate},
                  {color:'rgba(255,0,0,.17)',start:civ.Rate,end:100}]}>
            </ConicGradient>
          </div>
        </div>
        {/each}
      </div>

      <div class="flex items-center justify-between">
        {#each openMember.CivsOp1v1.slice(0, 20) as civ}
        <div class="justify-center p-1 rounded-lg">
          <div class="flex items-center justify-between p-1 rounded-lg bg-surface-800/30 w-28">
            <img class="h-6 me-2" src="{getCivUrl(civ.Name)}" alt="">
            <span class="badge variant-soft-surface">{civ.Matches}</span>
            <ConicGradient width="w-6 ms-2" stops=
            {[{color:'rgba(0,255,0,.17)',start:0,end:civ.Rate},
                {color:'rgba(255,0,0,.17)',start:civ.Rate,end:100}]}>
          </ConicGradient>
          </div>
          <span class="text-sm text-primary-100/50">{civ.Name}</span>
        </div>
        {/each}
      </div>

    </div>
  </section>   
 <!--------------------------------------------------------------------->

  </section>

{/if}



</main>

<style>
  .table tbody td {
    padding-left: 0;
    padding-right: 0;
    padding-top: 0;
    padding-bottom: 0;
    vertical-align: middle;
}
  .small-p {
    padding: 1em;
  }
  .cursor:hover {
    cursor: pointer;
  }
  .gradient-heading {
    @apply min-w-32 text-left;
    @apply ms-1 text-xl font-bold bg-gradient-to-br from-indigo-400 to-sky-200;
    @apply bg-clip-text text-transparent box-decoration-clone;
  }
  .activeRow {
    @apply bg-sky-700 bg-opacity-30;
  }
</style>
