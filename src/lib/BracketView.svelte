<script lang="ts">
  import { Avatar } from '@skeletonlabs/skeleton';
  import type { Bracket, BracketMatch, BracketSlot } from './bracket';

  interface Props {
    bracket: Bracket;
    nameLookUp: (id: string) => string;
    imageLookUp: (id: string) => string;
    onMatchClick?: (matchId: string) => void;
  }

  let { bracket, nameLookUp, imageLookUp, onMatchClick }: Props = $props();

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
</script>

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
            {@const clickable = Boolean(match.id && onMatchClick)}
            <button
              type="button"
              class="bracket-match text-left rounded-lg border border-surface-500 bg-surface-800/80 p-2 w-full
                     {clickable ? 'cursor-pointer hover:border-primary-400' : 'cursor-default'}
                     {match.label === 'Bye' ? 'opacity-80 border-dashed' : ''}"
              onclick={() => handleMatchClick(match)}
              disabled={!clickable}>
              {#if match.label && match.label !== 'Bye'}
                <div class="text-[10px] uppercase tracking-wide text-surface-400 mb-1">{match.label}</div>
              {/if}
              {#each match.slots as slot, si}
                <div
                  class="flex items-center gap-2 py-1 px-1 rounded
                         {si === 0 ? 'mb-1' : ''}
                         {slot.isBye ? 'text-surface-500' : ''}">
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
                </div>
                {#if si === 0}
                  <div class="border-t border-surface-600/60 my-0.5"></div>
                {/if}
              {/each}
            </button>
          {/each}
        </div>
      </div>

      {#if ri < bracket.rounds.length - 1}
        <div class="bracket-connector self-center text-surface-600 text-2xl select-none" aria-hidden="true">›</div>
      {/if}
    {/each}
  </div>

  {#if bracket.thirdPlace}
    {@const tp = bracket.thirdPlace}
    {@const clickable = Boolean(tp.id && onMatchClick)}
    <div class="mt-8 flex justify-center">
      <button
        type="button"
        class="bracket-match text-left rounded-lg border border-surface-500 bg-surface-800/80 p-2 min-w-[220px]
               {clickable ? 'cursor-pointer hover:border-primary-400' : 'cursor-default'}"
        onclick={() => handleMatchClick(tp)}
        disabled={!clickable}>
        <div class="text-[10px] uppercase tracking-wide text-surface-400 mb-1">Platz 3</div>
        {#each tp.slots as slot, si}
          <div class="flex items-center gap-2 py-1 px-1 {slot.isBye ? 'text-surface-500' : ''}">
            {#if slot.playerId}
              <Avatar width="w-6" initials={slotLabel(slot)} src={slotImage(slot)} />
            {:else}
              <div class="w-6 h-6 rounded-full bg-surface-700 shrink-0"></div>
            {/if}
            <span class="truncate text-sm flex-1">{slotLabel(slot)}</span>
            {#if scoreText(slot) !== ''}
              <span class="font-bold text-sm tabular-nums">{scoreText(slot)}</span>
            {/if}
          </div>
          {#if si === 0}
            <div class="border-t border-surface-600/60 my-0.5"></div>
          {/if}
        {/each}
      </button>
    </div>
  {/if}
</div>
