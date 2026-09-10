<script lang="ts">
  import "./app.css";

  import { Avatar } from '@skeletonlabs/skeleton';
  import { ConicGradient } from '@skeletonlabs/skeleton';
  import { onMount } from 'svelte';
  import type { Team, Member, StatItem } from './types'

  const BASE_URL = import.meta.env.BASE_URL;

  let data: Team[] = $state([]);
  let visibleTeams : string[] = $state([]);

  function mapTeamImage(teamname: string) {
    if ( teamname == "Noobelite" ) {
      return BASE_URL + "ne.webp"
    } 
    return BASE_URL + "placeholder.webp"
  }

  function getMapUrl(name: string): string {
    let url = "https://www.aoe2insights.com/static/images/maps/" + name.replace(" ", "_").toLowerCase() + ".webp"    
    return url;
  }

  function getCivUrl(name: string): string {
    let url = "https://www.aoe2insights.com/static/images/civs/" + name.replace(" ", "_").toLowerCase() + ".webp"    
    return url;
  }


  function teammate(team: Team, mate: StatItem) {
    let item = team.Members.find(member => mate.Name.toLowerCase().includes(member.Name.toLowerCase()))
    if ( item ) {
      return true
    }
    return false
  }

  function toggleMembers(name: string) {
    if ( visibleTeams.includes(name) ) {
      visibleTeams = visibleTeams.filter(s => s !== name);
    } else {
      visibleTeams.push(name)
    }
    visibleTeams = visibleTeams;
  }

  onMount(async () => {
    const response = await fetch(BASE_URL+'data.json');
    let fetchedData = await response.json();
    data = fetchedData.sort((a: Team, b: Team) => b.Elo - a.Elo)
    data.forEach((team: Team) => {
      team.Members.forEach((member: Member) => {
        let sorted1v1Maps: StatItem[] = [];
        if ( member.Maps1v1 !== undefined ) {
          sorted1v1Maps = member.Maps1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sortedTeamMaps: StatItem[] = [];
        if ( member.MapsTeam !== undefined ) {
          sortedTeamMaps = member.MapsTeam.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sorted1v1Civs: StatItem[] = [];
        if ( member.Civs1v1 !== undefined ) {
          sorted1v1Civs = member.Civs1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sortedTeamCivs: StatItem[] = [];
        if ( member.CivsTeam !== undefined ) {
          sortedTeamCivs = member.CivsTeam.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sorted1v1OpCivs: StatItem[] = [];
        if ( member.CivsOp1v1 !== undefined ) {
          sorted1v1OpCivs = member.CivsOp1v1.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        let sortedTeamOpCivs: StatItem[] = [];
        if ( member.CivsOpTeam !== undefined ) {
          sortedTeamOpCivs = member.CivsOpTeam.sort((a: StatItem, b: StatItem) => b.Matches - a.Matches);
        }
        member.Maps1v1 = sorted1v1Maps;
        member.MapsTeam = sortedTeamMaps;
        member.Civs1v1 = sorted1v1Civs;
        member.CivsTeam = sortedTeamCivs;
        member.CivsOp1v1 = sorted1v1OpCivs;
        member.CivsOpTeam = sortedTeamOpCivs;
        if ( member.TeamMates == undefined ) {
          member.TeamMates = []
        }
      })
      let sortedMembers = team.Members.sort((a: Member, b: Member) => b.EloTurn - a.EloTurn);
      team.Members = sortedMembers;
    })
  });
</script>


<main>
  <h1 class="mb-8">AoE2Germany 2v2 Liga - Season 6</h1>

  {#each data as team}
    <!-- Team header ---------------------------------------------------------->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="card card-hover mb-4 mt-4 small-p cursor"
      onclick={() => toggleMembers(team.Name)}>
      <header class="card-header p-0 mb-4">
        <section class="flex items-center justify-between w-full p-0">
          <div class="flex items-center space-x-4">
            <img class="h-20 max-w-full rounded-lg" src={mapTeamImage(team.Name)} alt="">
            <span class="text-xl font-bold">{team.Name}</span>
          </div>

          <!-- Team member overview ------------------------------------------->
          <div class="flex items-center space-x-4">
            {#each team.Members as member}
            <span class="text-sm justify-center">
                <Avatar width="w-12 m-auto" src={member.Image}/>
                {member.Name}</span>
            {/each}
          </div>
          <!------------------------------------------------------------------->

          <span class="flex text-xl">
            <span class="badge variant-ghost-surface me-2">TeamElo</span>
            {team.Elo}
          </span>
        </section>
      </header>

      {#each team.Members as member}
      {#if visibleTeams.includes(team.Name)}
      
      <!-- Member header ---------------------------------------------------->
      <section class="mb-4 small-p rounded-lg border border-surface-500 bg-surface-900/50">
        <section class="flex items-center justify-between w-full p-0">
          <div class="flex items-center space-x-4">
            <Avatar width="w-12" src={member.Image}/>
            <span class="text-l">{member.Name}</span>  
          </div>

          <div class="flex items-center space-x-2">
            <span class="badge variant-ghost-surface">{member.FlankRate}%</span>  
            <img class="h-14 max-w-full rounded-lg border border-surface-500" src="{BASE_URL}flank.webp" alt="">
            <img class="h-14 max-w-full rounded-lg border border-surface-500" src="{BASE_URL}pocket.webp" alt="">
            <span class="badge variant-ghost-surface">{member.PocketRate}%</span>  
          </div>

          <div class="flex items-center">
            <span class="badge variant-ghost-surface me-2">1v1</span>
            <div class="card grid w-24 h-20 small-p items-center">
              <span class="text-m">{member.Elo1v1}</span>
              <span class="text-m">({member.Ath1v1})</span>
            </div>
              <span class="badge variant-ghost-surface me-2 ms-2">Team</span>
              <div class="card grid w-24 h-20 small-p items-center">
                <span class="text-m">{member.EloTeam}</span>
                <span class="text-m">({member.AthTeam})</span>
              </div>
            <span class="badge variant-ghost-surface me-1 ms-2">TurnElo</span>
            <span class="text-l w-12 items-end">{member.EloTurn}</span>
          </div>
        </section>

        <!-- Teammates details ------------------------------------------------>
        <section class="flex items-center justify-between w-full p-2 mt-2 mb-2 bg-surface-900/60 rounded-lg">
          <span class="gradient-heading">
              Teammates
          </span>
            {#each member.TeamMates.slice(0, 10) as mate}
            <span class="relative justify-center p-1 rounded-lg {teammate(team, mate)?"bg-surface-800/80":""}">
              <span class="truncate overflow-hidden text-sm {teammate(team, mate)?"font-bold":""}">{mate.Name}</span>
              <ConicGradient width="w-12" stops=
              {[{color:'rgba(0,255,0,.25)',start:0,end:mate.Rate},
                    {color:'rgba(255,0,0,.25)',start:mate.Rate,end:100}]}>
              </ConicGradient>
              <span class="font-bold absolute inset-y-1/2 inset-x-1/4">{mate.Matches}</span>
            </span>
            {/each}
        </section>
        <!--------------------------------------------------------------------->

        <!-- Team maps and civs ----------------------------------------------->
        <section class="flex items-center justify-between w-full p-2 mt-2 bg-surface-900/60 rounded-lg">
          <span class="gradient-heading">
              Team Maps
          </span>
          {#each member.MapsTeam.slice(0, 7) as map}
          <div class="justify-center p-1 rounded-lg">
            <span class="text-sm text-primary-100/80">{map.Name}</span>
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
        <section class="flex items-center w-full p-2 mb-2 bg-surface-900/60 rounded-lg">
          <span class="gradient-heading">
              Team Civs
          </span>

          <div class="snap-x scroll-px-4 snap-mandatory scroll-smooth overflow-x-auto">
            <div class="flex items-center justify-between w-full">
              {#each member.CivsTeam.slice(0, 20) as civ}
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
              {#each member.CivsOpTeam.slice(0, 20) as civ}
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

        <!-- 1v1 maps and civs ------------------------------------------------>
        <section class="flex items-center justify-between w-full p-2 mt-2 bg-surface-900/60 rounded-lg">
          <span class="gradient-heading">
              1v1 Maps
          </span>
          {#each member.Maps1v1.slice(0, 7) as map}
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

        <section class="flex items-center w-full p-2 mb-2 bg-surface-900/60 rounded-lg">
          <span class="gradient-heading">
              1v1 Civs
          </span>

          <div class="snap-x scroll-px-4 snap-mandatory scroll-smooth overflow-x-auto">
            <div class="flex items-center justify-between w-full">
              {#each member.Civs1v1.slice(0, 20) as civ}
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
              {#each member.CivsOp1v1.slice(0, 20) as civ}
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
        </section>        <!--------------------------------------------------------------------->

        </section>
      <!----------------------------------------------------------------------->

      {/if}
      {/each}

    </div>
  {/each}

</main>

<style>
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
</style>
