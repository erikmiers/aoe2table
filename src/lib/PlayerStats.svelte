<script lang="ts">

    import { type DraftAnalysis, type Stage, type Match, type Member, type GameAnalysis, 
        type DraftObject, type CompanionGameObject, type DraftEvent } from '../types';
    import { draftCache } from './draftCache';
    
    import { Avatar } from '@skeletonlabs/skeleton';
    import { fade, slide } from 'svelte/transition';
    import { ConicGradient } from '@skeletonlabs/skeleton';
    
    export interface Props {
        openMember : Member | undefined;
        stages : Stage[];
        lookup: (lid: string) => Member | undefined;
    }

    let {openMember, stages, lookup} : Props = $props()
    let draftAnalysis: Array<DraftAnalysis> | undefined = $state(undefined)

    $effect(() => {
        draftAnalysis = openMember ? draftCache.get(openMember.LeagueID) : undefined;
    });
    
    const mapIcons: Record<string,string> = {
        Badlands: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Badlands.png",
        Basmo: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Basmo.png",
        Copenhagen: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Copenhagen.png",
        Moats: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Moats.png",
        "Monte Pascoal": "https://files.aoe2germany.de/files/maps-draft/1v1_10_Monte_Pascoal.png",
        Nomad: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Nomad.png",
        Seychelles: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Seychelles.png",
        Shoals: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Shoals.png",
        Typhoon: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Typhoon.png",
        Valley: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Valley.png",
        Vulpine: "https://files.aoe2germany.de/files/maps-draft/1v1_10_Vulpine.png",
        ZeWall: "https://files.aoe2germany.de/files/maps-draft/1v1_10_ZeWall.png"
     }

//  <!-- 1v1 maps and civs ------------------------------------------------>
//   <section class="flex items-center justify-between w-full p-2 mt-2 bg-surface-900/60 rounded-lg"
//   transition:slide={{ duration: 300 }}
//   >
//     <span class="gradient-heading">
//         1v1 Maps
//     </span>
//     {#each openMember.Maps1v1.slice(0, 7) as map}
//     <div class="justify-center p-1 rounded-lg">
//       <span class="text-sm">{map.Name}</span>
//       <div class="flex items-center relative rounded-lg border border-surface-500">
//         <img class="h-14 me-2" src="{getMapUrl(map.Name)}" alt="">
//         <ConicGradient width="w-12" stops=
//         {[{color:'rgba(0,255,0,.17)',start:0,end:map.Rate},
//               {color:'rgba(255,0,0,.17)',start:map.Rate,end:100}]}>
//         </ConicGradient>
//         <div class="absolute inset-y-1/2 inset-x-1/4">
//           <span class="badge variant-soft-surface">{map.Matches}</span>
//         </div>
//       </div>
//     </div>
//     {/each}
//   </section>

//   <section class="flex items-center w-full p-2 mb-2 bg-surface-900/60 rounded-lg"
//   transition:slide={{ duration: 300 }}
//   >
//     <span class="gradient-heading">
//         1v1 Civs
//     </span>

//     <div class="snap-x scroll-px-4 snap-mandatory scroll-smooth overflow-x-auto">
//       <div class="flex items-center justify-between w-full">
//         {#each openMember.Civs1v1.slice(0, 20) as civ}
//         <div class="justify-center p-1 rounded-lg">
//           <span class="text-sm text-primary-100/50">{civ.Name}</span>
//           <div class="flex items-center justify-between p-1 rounded-lg bg-surface-900 w-28">
//             <img class="h-6 me-2" src="{getCivUrl(civ.Name)}" alt="">
//             <span class="badge variant-soft-surface">{civ.Matches}</span>
//             <ConicGradient width="w-6 ms-2" stops=
//             {[{color:'rgba(0,255,0,.17)',start:0,end:civ.Rate},
//                   {color:'rgba(255,0,0,.17)',start:civ.Rate,end:100}]}>
//             </ConicGradient>
//           </div>
//         </div>
//         {/each}
//       </div>

//       <div class="flex items-center justify-between">
//         {#each openMember.CivsOp1v1.slice(0, 20) as civ}
//         <div class="justify-center p-1 rounded-lg">
//           <div class="flex items-center justify-between p-1 rounded-lg bg-surface-800/30 w-28">
//             <img class="h-6 me-2" src="{getCivUrl(civ.Name)}" alt="">
//             <span class="badge variant-soft-surface">{civ.Matches}</span>
//             <ConicGradient width="w-6 ms-2" stops=
//             {[{color:'rgba(0,255,0,.17)',start:0,end:civ.Rate},
//                 {color:'rgba(255,0,0,.17)',start:civ.Rate,end:100}]}>
//           </ConicGradient>
//           </div>
//           <span class="text-sm text-primary-100/50">{civ.Name}</span>
//         </div>
//         {/each}
//       </div>

//     </div>
//   </section>   
//  <!--------------------------------------------------------------------->    

let isLoading : boolean = $state(false);

//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
function findMatchesByPlayerId(playerId: string): Match[] {
  const matches = stages
    .flatMap(stage => stage.groups)
    .flatMap(group => group.rounds)
    .flatMap(round => round.matches)
    .filter(match =>
      match.opponents.some(opponent => opponent.id === playerId)
    );

  return [...new Map(matches.map(match => [match.id, match])).values()];
}      
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
async function fetchDrafts(matches: Match[]): Promise<Map<string, DraftObject>> {
  const draftIds = new Set<string>();

  for (const match of matches) {
    if ( match.meta ) {
      if (match.meta.civs) draftIds.add(match.meta.civs);  
      if (match.meta.maps) draftIds.add(match.meta.maps);  
    }
  }

  const drafts = await Promise.all(
    [...draftIds].map(async id => {
      const response = await fetch(
        `https://aoe2cm.net/api/draft/${encodeURIComponent(id)}`
      );

      if (!response.ok) {
        console.log(`Failed to fetch draft ${id}: ${response.status}`);
        return [id, {} as DraftObject] as const;
      }

      return [id, await response.json() as DraftObject] as const;
    })
  );

  return new Map(drafts);
}
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
async function fetchGames(matches: Match[]): Promise<Array<CompanionGameObject>> {
    const playerIds = new Set<[string, string]>();

    for (const match of matches) {
        const host = match.opponents[0]
        const guest = match.opponents[1]
        const hostId = lookup(host?.id ?? "")?.RelicID ?? "";
        const guestId = lookup(guest?.id ?? "")?.RelicID ?? "";
        playerIds.add([hostId, guestId])
    }
  
    const games = await Promise.all(
        [...playerIds].map(async ([hostId, guestId]) => {
            
            if ( !hostId || !guestId ) {
                console.log("Skipping game fetching for ids", hostId, guestId)
                return {} as CompanionGameObject;
            } 

        const response = await fetch(
            `https://data.aoe2companion.com/api/matches?profile_ids=${encodeURIComponent(hostId)}&with_profile_ids=${encodeURIComponent(guestId)}&language=en`
        );

        
        if (!response.ok) {
            console.log(`Failed to fetch games for ${hostId} vs ${guestId}: ${response.status}`);
            return {} as CompanionGameObject;
            }
            
        return await response.json() as CompanionGameObject;
        })
    );

    return games;
}
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
function getDraftEvents(events: Array<DraftEvent>, player: string, action: string): Array<string> {
    let draftEvents: Array<string> = [];
    if ( !events || events.length <= 0 ) {
        return draftEvents
    }

    events.forEach( event => {
        if ( event.player === player && event.actionType === action ) {
            draftEvents.push(event.chosenOptionId)
        }
    });

    return draftEvents;
}
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
async function loadDrafts() {
    if ( !openMember ) {
        return
    }

    isLoading = true;

    const matches = findMatchesByPlayerId(openMember.LeagueID);
    const drafts = await fetchDrafts(matches);
    const games = await fetchGames(matches);

    draftAnalysis = [];
    for (const [index, match] of matches.entries()) {
        if ( !match.meta ) {
            continue;
        }

        const hostId = lookup(match.opponents[0]?.id ?? "")?.RelicID ?? "";

        let analysis = {} as DraftAnalysis;
        if ( match.meta.maps ) {
            const mapDraft = drafts.get(match.meta.maps);
            if ( mapDraft ) {
                analysis.hostName = mapDraft.nameHost;
                analysis.guestName = mapDraft.nameGuest;
                analysis.hostMaps = getDraftEvents(mapDraft.events, "HOST", "pick");
                analysis.guestMaps = getDraftEvents(mapDraft.events, "GUEST", "pick");
                analysis.hostMapSnipes = getDraftEvents(mapDraft.events, "HOST", "snipe");
                analysis.guestMapSnipes = getDraftEvents(mapDraft.events, "GUEST", "snipe");
            }
        }

        if ( match.meta.civs ) {
            const civDraft = drafts.get(match.meta.civs);
            if ( civDraft ) {
                analysis.hostCivs = getDraftEvents(civDraft.events, "HOST", "pick");
                analysis.guestCivs = getDraftEvents(civDraft.events, "GUEST", "pick");
            }
        }

        const gameData = games[index];
        if ( !gameData || !gameData.matches || gameData.matches.length <= 0) {
            console.log("Skipping gameData", gameData)
            draftAnalysis.push(analysis);
            continue;
        }

        if ( !analysis.hostMaps || !analysis.guestMaps ) {
            console.log("Skipping map draft")
            draftAnalysis.push(analysis);
            continue;
        }

        let playedHostMaps = analysis.hostMaps.flatMap((map) => 
            (analysis.guestMapSnipes.includes(map)?[]:[map]));

        let playedGuestMaps = analysis.guestMaps.flatMap((map) => 
            (analysis.hostMapSnipes.includes(map)?[]:[map]));

        const playedMaps = [...playedHostMaps, ...playedGuestMaps];

        const gameEntries : Array<GameAnalysis> = []
        for( const game of gameData.matches ) {
            const gameId = game.matchId;
            const mapName = game.mapName;
            let homePlayer = game.teams[0].players[0];
            let guestPlayer = game.teams[1].players[0];
            const started = new Date(game.started);
            const finished = new Date(game.finished);
            const durationMs = finished.getTime() - started.getTime();
            const totalMinutes = Math.floor(durationMs / 60_000);
            const map = playedMaps.find(map => mapName.includes(map));
            if ( guestPlayer.profileId === hostId ) {
                [homePlayer, guestPlayer] = [guestPlayer, homePlayer]
            }

            if ( map ) {
                const entry : GameAnalysis = {
                    companionId: game.matchId,
                    companionLink: "https://www.aoe2companion.com/players/"+hostId+"/matches/"+game.matchId,
                    downloadLink: "https://api.ageofempires.com/api/GameStats/AgeII/GetMatchReplay/?matchId="+game.matchId+"&profileId="+hostId,
                    map: map,
                    hostCiv: homePlayer.civName,
                    guestCiv: guestPlayer.civName,
                    hostCivImage: homePlayer.civImageUrl,
                    guestCivImage: guestPlayer.civImageUrl,
                    winner: homePlayer.won? homePlayer.name : guestPlayer.name,
                    looser: homePlayer.won? guestPlayer.name : homePlayer.name,
                    hostWin: homePlayer.won,
                    startTime: started,
                    duration: totalMinutes
                }

                gameEntries.push(entry)
            }
        }

        analysis.games = gameEntries;
        draftAnalysis.push(analysis);
    }

    isLoading = false;
    console.log(draftAnalysis)
    draftCache.set(openMember.LeagueID, draftAnalysis)
}
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
function sortedMatches(matches: Array<GameAnalysis>): Array<GameAnalysis> {
    if ( !matches || matches.length <=0 ) {
        return []
    }

    return [...matches].sort((a,b) => a.startTime.getTime() - b.startTime.getTime())
}
//----------------------------------------------------------------------------->    




//----------------------------------------------------------------------------->    
</script>
<!----------------------------------------------------------------------------->




<!----------------------------------------------------------------------------->
{#if openMember !== undefined}

 <!-- Member header ---------------------------------------------------->
<section class="mb-4 mt-8 p-[1em] rounded-lg border border-surface-500 bg-surface-900/50">
    <section class="flex items-center justify-between w-full p-0 pb-4">
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
        <div class="card !p-[1em] items-center">
            <span class="text-m">{openMember.Elo1v1}</span>
            <span class="text-m text-primary-100/50">&nbsp;{openMember.Ath1v1}</span>
        </div>
            <span class="badge variant-ghost-surface me-2 ms-2">Team</span>
            <div class="card !p-[1em] items-center">
                <span class="text-m">{openMember.EloTeam}</span>
                <span class="text-m text-primary-100/50">&nbsp;{openMember.AthTeam}</span>
            </div>
            <!-- <button type="button" class="btn-icon variant-ghost m-4 font-medium text-2xl"
            on:click={() => toggleMembers(player.Name)}> {openMembers.includes(player.Name)?"-":"+"}</button> -->
        </div>        
    </section>
    <button type="button" class="btn btn-sm variant-ghost-primary ms-2 me-auto" onclick={(e) => loadDrafts()}>
        {#if isLoading}
            <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        {:else}
            <span>Load drafts</span>
        {/if}
    </button>
    {#if draftAnalysis}
        <section class="flex items-start overflow-x-auto max-w-full mt-4 p-0">
        {#each draftAnalysis as draft, round}

            <div class="card !p-[1em] items-center !w-[400px] m-1 shrink-0">
                <div class="flex justify-content-between w-[300px] mb-2">
                    <span class="badge variant-ghost-surface me-auto">{draft.hostName}</span>
                    <span class="text-slate-600">Round {round+1}</span>
                    <span class="badge variant-ghost-surface ms-auto">{draft.guestName}</span>
                </div>
                <div class="flex justify-content-between ms-0">
                    {#each draft.hostMaps as map}
                    <div class="relative me-auto ms-0">
                        <img class="size-14 overflow-hidden rounded-full {draft.guestMapSnipes.includes(map)?'grayscale':''}" 
                            src={mapIcons[map]} alt={map} />
                        <span class="absolute bottom-0 left-0 w-full truncate text-center text-xs bg-surface-800/50">{map}</span>
                    </div>
                    {/each}
                    {#each draft.guestMaps as map}
                    <div class="relative ms-auto me-0">
                        <img class="size-14 overflow-hidden rounded-full {draft.hostMapSnipes.includes(map)?'grayscale':''}" 
                            src={mapIcons[map]} alt={map} />
                        <span class="absolute bottom-0 left-0 w-full truncate text-center text-xs bg-surface-800/50">{map}</span>
                    </div>
                    {/each}
                </div>
                <div class="flex justify-content-between ms-0 pt-2">
                    {#each draft.hostCivs as civ} 
                        <img class="size-8 overflow-hidden rounded-full ms-0 me-auto" 
                        src="https://backend.cdn.aoe2companion.com/public/aoe2/de/civilizations/{civ.toLowerCase()}.png" alt={civ} />
                    {/each}
                    {#each draft.guestCivs as civ} 
                        <img class="size-8 overflow-hidden rounded-full ms-auto me-0" 
                        src="https://backend.cdn.aoe2companion.com/public/aoe2/de/civilizations/{civ.toLowerCase()}.png" alt={civ} />
                    {/each}
                </div>

                {#each sortedMatches(draft.games) as game}
                <div class="flex justify-content-between ms-0 mt-2 border border-slate-700 rounded-md">
                    
                    <img class="size-10 overflow-hidden rounded-full m-auto {game.hostWin?'':'grayscale'}" 
                        src={game.hostCivImage} alt={game.hostCiv} />

                    <div class="relative m-auto">
                        <img class="size-14 overflow-hidden rounded-full" src={mapIcons[game.map]} alt={game.map} />
                        <span class="absolute top-0 left-0 w-full truncate text-center text-xs bg-surface-800/80">{game.duration}m</span>
                        <span class="absolute bottom-0 left-0 w-full truncate text-center text-xs bg-surface-800/50">{game.map}</span>
                    </div>

                    <img class="size-10 overflow-hidden rounded-full m-auto {game.hostWin?'grayscale':''}" 
                        src={game.guestCivImage} alt={game.guestCiv} />

                    <div class="grid row-2 me-2 p-0 place-self-center">
                        <a href={game.companionLink} target="_blank"
                            class="btn-icon btn-sm size-5 variant-ghost-surface mt-1" aria-label="link">
                            <svg xmlns="http://www.w3.org/2000/svg" height="12px" viewBox="0 -960 960 960" width="12px" fill="#9da4a8">
                                <path d="M318-120q-82 0-140-58t-58-140q0-40 15-76t43-64l134-133 56 56-134 134q-17 17-25.5 38.5T200-318q0 49 34.5 83.5T318-200q23 0 45-8.5t39-25.5l133-134 57 57-134 133q-28 28-64 43t-76 15Zm79-220-57-57 223-223 57 57-223 223Zm251-28-56-57 134-133q17-17 25-38t8-44q0-50-34-85t-84-35q-23 0-44.5 8.5T558-726L425-592l-57-56 134-134q28-28 64-43t76-15q82 0 139.5 58T839-641q0 39-14.5 75T782-502L648-368Z"/>
                            </svg>
                        </a>
                        <a href={game.downloadLink} target="_blank"
                            class="btn-icon btn-sm size-5 variant-ghost-surface mt-1 mb-1" aria-label="link">
                            <svg xmlns="http://www.w3.org/2000/svg" height="12px" viewBox="0 -960 960 960" width="12px" fill="#9da4a8">
                                <path d="M480-320 280-520l56-58 104 104v-326h80v326l104-104 56 58-200 200ZM240-160q-33 0-56.5-23.5T160-240v-120h80v120h480v-120h80v120q0 33-23.5 56.5T720-160H240Z"/>
                            </svg>                  
                        </a>

                    </div>
                </div>
                {/each}
            </div>           
        {/each}
        </section>
    {/if}
</section>
{/if}