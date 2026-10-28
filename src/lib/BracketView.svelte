<script lang="ts">
  import { Avatar } from '@skeletonlabs/skeleton';
  import type { Bracket, BracketMatch, BracketSlot } from './bracket';

  interface Props {
    bracket: Bracket;
    nameLookUp: (id: string) => string;
    imageLookUp: (id: string) => string;
    onMatchClick?: (matchId: string) => void;
    onPlayerClick?: (playerId: string) => void;
    selectedPlayerId?: string;
  }

  let { bracket, nameLookUp, imageLookUp, onMatchClick, onPlayerClick, selectedPlayerId }: Props = $props();

  function slotLabel(slot: BracketSlot): string {
    if (slot.isBye) return 'Bye';
    if (slot.playerId) return nameLookUp(slot.playerId);
    if (slot.seed) return `Seed ${slot.seed}`;
    return 'TBD';
  }

  function slotImage(slot: BracketSlot): string | undefined {
    if (slot.playerId) return imageLookUp(slot.playerId);
    return undefined;
  }

  function scoreText(slot: BracketSlot): string {
    if (slot.score === undefined || slot.score === null) return '';
    return String(slot.score);
  }

  function handleMatchClick(m: BracketMatch) {
    if (m.id && onMatchClick) {
      onMatchClick(m.id);
    }
  }

  function selectPlayer(event: MouseEvent, playerId: string) {
    event.stopPropagation();
    onPlayerClick?.(playerId);
  }
</script>

{#snippet slotContents(slot: BracketSlot)}
  {#if slot.playerId}
    <Avatar width="w-6" initials={slotLabel(slot)} src={slotImage(slot)} />
  {:else}
    <div class="w-6 h-6 rounded-full bg-surface-700 shrink-0"></div>
  {/if}
  <span class="truncate text-sm flex-1">
    {#if slot.seed && slot.playerId}
      <span class="text-surface-500 text-xs me-1">#{slot.seed}</span>
    {/if}
    {slotLabel(slot)}
  </span>
  {#if scoreText(slot) !== ''}
    <span class="font-bold text-sm tabular-nums">{scoreText(slot)}</span>
  {/if}
{/snippet}

{#snippet playerSlot(slot: BracketSlot)}
  {#if slot.playerId && onPlayerClick}
    <button
      type="button"
      class="slot-player"
      class:is-selected={slot.playerId === selectedPlayerId}
      aria-pressed={slot.playerId === selectedPlayerId}
      onclick={(event) => selectPlayer(event, slot.playerId!)}>
      {@render slotContents(slot)}
    </button>
  {:else}
    <div class="flex items-center gap-2 py-1 px-1 rounded {slot.isBye ? 'text-surface-500' : ''}">
      {@render slotContents(slot)}
    </div>
  {/if}
{/snippet}

{#snippet matchCard(match: BracketMatch, heading: string | undefined, widthClass: string)}
  {@const clickable = Boolean(match.id && onMatchClick)}
  <div
    class="bracket-match relative text-left rounded-lg border border-surface-500 bg-surface-800/80 p-2 {widthClass}
           {match.label === 'Bye' ? 'opacity-80 border-dashed' : ''}
           {clickable ? 'has-[.match-hit:hover]:border-primary-400 has-[.match-hit:focus-visible]:border-primary-400' : ''}">
    {#if clickable}
      <button
        type="button"
        class="match-hit"
        aria-label={heading ? `Open ${heading}` : 'Open match'}
        onclick={() => handleMatchClick(match)}>
      </button>
    {/if}
    <div class="relative z-10 pointer-events-none">
      {#if heading}
        <div class="text-[10px] uppercase tracking-wide text-surface-400 mb-1">{heading}</div>
      {/if}
      {#each match.slots as slot, si}
        {@render playerSlot(slot)}
        {#if si === 0}
          <div class="border-t border-surface-600/60 my-0.5"></div>
        {/if}
      {/each}
    </div>
  </div>
{/snippet}

{#if bracket.isPreview}
  <p class="text-sm text-surface-400 mb-4 text-center">
    Preview bracket from current Swiss standings (top {bracket.spots}) — not yet seeded on Toornament.
  </p>
{/if}

<div class="bracket-scroll overflow-x-auto w-full pb-4">
  <div class="bracket-board inline-flex gap-8 items-stretch min-w-min px-2">
    {#each bracket.rounds as round, ri}
      <div class="bracket-round flex flex-col justify-around gap-4 min-w-[220px]">
        <h3 class="text-sm font-bold text-surface-300 text-center sticky top-0 bg-surface-900/80 py-1 rounded">
          {round.name}
        </h3>
        <div
          class="flex flex-col flex-1 justify-around gap-6"
          style="min-height: {Math.max(round.matches.length, 1) * 5.5}rem">
          {#each round.matches as match}
            {@render matchCard(match, match.label && match.label !== 'Bye' ? match.label : undefined, 'w-full')}
          {/each}
        </div>
      </div>

      {#if ri < bracket.rounds.length - 1}
        <div class="bracket-connector self-center text-surface-600 text-2xl select-none" aria-hidden="true">›</div>
      {/if}
    {/each}
  </div>

  {#if bracket.thirdPlace}
    <div class="mt-8 flex justify-center">
      {@render matchCard(bracket.thirdPlace, 'Platz 3', 'min-w-[220px]')}
    </div>
  {/if}
</div>

<style>
  .match-hit {
    position: absolute;
    inset: 0;
    z-index: 0;
    margin: 0;
    padding: 0;
    border: 0;
    border-radius: inherit;
    background: transparent;
    cursor: pointer;
  }
  .match-hit:hover,
  .match-hit:focus-visible {
    border-color: transparent;
  }
  .slot-player {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    margin: 0;
    padding: 0.25rem;
    border: 0;
    border-radius: 0.25rem;
    background: transparent;
    font: inherit;
    color: inherit;
    text-align: left;
    cursor: pointer;
    pointer-events: auto;
    position: relative;
    z-index: 1;
  }
  .slot-player:hover {
    border-color: transparent;
    background: rgb(3 105 161 / 0.2);
  }
  .slot-player.is-selected {
    background: rgb(3 105 161 / 0.3);
  }
</style>
