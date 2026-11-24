<script lang="ts">
    import { bannedCivs, bannedMaps, snipedMaps, pickedCivs, pickedMaps, boardKey, readBoard, writeBoard, prunePlacements, pruneWinners, guessTeamSize, parsePlacement, formatPlacement, type BoardPick, type WinnerSide } from './board';
    import { watchDraft } from './liveDraft';
    import { emptyWatched, parseDraftId, type DraftStatus, type WatchedDraft } from './types';

    const baseUrl = import.meta.env.BASE_URL;

    function queryValue(key: string): string {
        if (typeof location === 'undefined') return '';
        return new URLSearchParams(location.search).get(key) ?? '';
    }

    let mapInput = $state(queryValue('maps'));
    let civInput = $state(queryValue('civs'));
    let loadedMapId = $state(parseDraftId(queryValue('maps')));
    let loadedCivId = $state(parseDraftId(queryValue('civs')));
    let loadNonce = $state(0);
    let inputError = $state('');
    let mapDraft = $state<WatchedDraft>(emptyWatched());
    let civDraft = $state<WatchedDraft>(emptyWatched());
    let placements = $state<Record<string, string>>({});
    let winners = $state<Record<string, WinnerSide>>({});
    let dragId = $state('');
    let dropTarget = $state('');
    let brokenMaps = $state<Record<string, boolean>>({});

    let mapId = $derived(loadedMapId);
    let civId = $derived(loadedCivId);
    let maps = $derived(pickedMaps(mapDraft.state));
    let civs = $derived(pickedCivs(civDraft.state));
    let bans = $derived(bannedCivs(civDraft.state));
    let mapBans = $derived(bannedMaps(mapDraft.state));
    let mapSnipes = $derived(snipedMaps(mapDraft.state));
    let civById = $derived(new Map(civs.map((civ) => [civ.id, civ])));
    let nameHost = $derived(mapDraft.state?.nameHost || civDraft.state?.nameHost || 'Host');
    let nameGuest = $derived(mapDraft.state?.nameGuest || civDraft.state?.nameGuest || 'Guest');
    let hostStack = $derived(civs.filter((civ) => civ.picker === 'HOST' && placements[civ.id] === undefined));
    let guestStack = $derived(civs.filter((civ) => civ.picker === 'GUEST' && placements[civ.id] === undefined));
    let hostBans = $derived(bans.filter((civ) => civ.picker === 'HOST'));
    let guestBans = $derived(bans.filter((civ) => civ.picker === 'GUEST'));
    let adminBans = $derived(bans.filter((civ) => civ.picker === 'NONE'));
    let hostMapOnly = $derived(mapBans.filter((map) => map.picker === 'HOST'));
    let guestMapOnly = $derived(mapBans.filter((map) => map.picker === 'GUEST'));
    let adminMapOnly = $derived(mapBans.filter((map) => map.picker === 'NONE'));
    let hostSnipes = $derived(mapSnipes.filter((map) => map.picker === 'HOST'));
    let guestSnipes = $derived(mapSnipes.filter((map) => map.picker === 'GUEST'));
    let adminSnipes = $derived(mapSnipes.filter((map) => map.picker === 'NONE'));
    let orderedMaps = $derived([
        ...maps.filter((map) => winners[map.id] == null),
        ...maps.filter((map) => winners[map.id] != null),
    ]);
    let hostScore = $derived(maps.reduce((count, map) => count + (winners[map.id] === 'HOST' ? 1 : 0), 0));
    let guestScore = $derived(maps.reduce((count, map) => count + (winners[map.id] === 'GUEST' ? 1 : 0), 0));
    let teamSize = $state(1);
    let teamSizeManual = $state(false);
    let guessedTeamSize = $derived(guessTeamSize([mapDraft.state?.preset.name, civDraft.state?.preset.name]));
    let slotList = $derived(Array.from({ length: teamSize }, (_, index) => index));

    let loadedKey = '';

    $effect(() => {
        const params = new URLSearchParams(location.search);
        if (mapId) params.set('maps', mapId);
        else params.delete('maps');
        if (civId) params.set('civs', civId);
        else params.delete('civs');
        const next = params.toString();
        const current = location.search.replace(/^\?/, '');
        if (next !== current) {
            history.replaceState(null, '', next ? `${location.pathname}?${next}` : location.pathname);
        }
    });

    $effect(() => {
        const id = loadedMapId;
        const nonce = loadNonce;
        let disconnect = () => {};
        if (!id) {
            mapDraft = emptyWatched();
            return;
        }
        mapDraft = { id, status: 'connecting', state: null, error: null };
        disconnect = watchDraft(id, (draft) => {
            if (nonce !== loadNonce) return;
            mapDraft = draft;
        });
        return () => disconnect();
    });

    $effect(() => {
        const id = loadedCivId;
        const nonce = loadNonce;
        let disconnect = () => {};
        if (!id) {
            civDraft = emptyWatched();
            return;
        }
        civDraft = { id, status: 'connecting', state: null, error: null };
        disconnect = watchDraft(id, (draft) => {
            if (nonce !== loadNonce) return;
            civDraft = draft;
        });
        return () => disconnect();
    });

    $effect(() => {
        const key = boardKey(loadedMapId, loadedCivId);
        if (key === loadedKey) return;
        loadedKey = key;
        const saved = readBoard(key);
        placements = saved.placements;
        winners = saved.winners;
        teamSizeManual = saved.teamSize != null;
        if (saved.teamSize) teamSize = saved.teamSize;
    });

    $effect(() => {
        if (teamSizeManual) return;
        teamSize = guessedTeamSize;
    });

    $effect(() => {
        if ((loadedMapId && !ready(mapDraft)) || (loadedCivId && !ready(civDraft))) return;
        const mapIds = new Set(maps.map((map) => map.id));
        const civIds = new Set(civs.map((civ) => civ.id));
        const nextPlacements = prunePlacements(placements, mapIds, civIds, teamSize);
        const nextWinners = pruneWinners(winners, mapIds);
        if (nextPlacements !== placements || nextWinners !== winners) {
            persist(nextPlacements, nextWinners);
        }
    });

    function loadDrafts() {
        const mapsId = parseDraftId(mapInput);
        const civsId = parseDraftId(civInput);
        if (mapInput.trim() && !mapsId) {
            inputError = 'Could not read a map draft id from that link.';
            return;
        }
        if (civInput.trim() && !civsId) {
            inputError = 'Could not read a civ draft id from that link.';
            return;
        }
        if (!mapsId && !civsId) {
            inputError = 'Paste a draft id or an aoe2cm draft link.';
            return;
        }
        inputError = '';
        loadedMapId = mapsId;
        loadedCivId = civsId;
        loadNonce += 1;
    }

    function ready(draft: WatchedDraft): boolean {
        return (draft.status === 'live' || draft.status === 'finished') && draft.state !== null;
    }

    function statusLabel(status: DraftStatus): string {
        switch (status) {
            case 'connecting': return 'Connecting';
            case 'live': return 'Live';
            case 'finished': return 'Finished';
            case 'missing': return 'Not found';
            case 'error': return 'No connection';
            default: return '';
        }
    }

    function statusClass(status: DraftStatus): string {
        switch (status) {
            case 'live': return 'text-emerald-300';
            case 'connecting': return 'text-amber-300';
            case 'missing':
            case 'error': return 'text-red-300';
            default: return 'text-surface-300';
        }
    }

    function placedCiv(mapPickId: string, side: 'HOST' | 'GUEST', slot: number): BoardPick | undefined {
        for (const [civPickId, placed] of Object.entries(placements)) {
            const parsed = parsePlacement(placed);
            if (parsed.mapId !== mapPickId || parsed.slot !== slot) continue;
            const civ = civById.get(civPickId);
            if (civ?.picker === side) return civ;
        }
        return undefined;
    }

    function hasSideCiv(mapPickId: string, side: 'HOST' | 'GUEST'): boolean {
        return slotList.some((slot) => placedCiv(mapPickId, side, slot) !== undefined);
    }

    function dropClass(side: 'HOST' | 'GUEST', mapPickId: string, slot: number): string {
        if (dropTarget !== `slot:${mapPickId}:${side}:${slot}`) return 'border-surface-600';
        return side === 'HOST' ? 'is-host-drop' : 'is-guest-drop';
    }

    function persist(
        nextPlacements: Record<string, string>,
        nextWinners: Record<string, WinnerSide>,
    ) {
        placements = nextPlacements;
        winners = nextWinners;
        writeBoard(boardKey(loadedMapId, loadedCivId), {
            placements: nextPlacements,
            winners: nextWinners,
            ...(teamSizeManual ? { teamSize } : {}),
        });
    }

    function chooseTeamSize(raw: string) {
        const size = Number(raw);
        if (size < 1 || size > 4) return;
        teamSizeManual = true;
        teamSize = size;
        persist(placements, winners);
    }

    function resetBoard() {
        if (Object.keys(placements).length === 0 && Object.keys(winners).length === 0) return;
        persist({}, {});
    }

    function toggleWinner(mapPickId: string, side: WinnerSide) {
        const next = { ...winners };
        if (next[mapPickId] === side) delete next[mapPickId];
        else next[mapPickId] = side;
        persist(placements, next);
    }

    function civResult(civ: BoardPick): 'win' | 'loss' | '' {
        const placed = placements[civ.id];
        if (!placed) return '';
        const mapPickId = parsePlacement(placed).mapId;
        const winner = winners[mapPickId];
        if (!winner) return '';
        return winner === civ.picker ? 'win' : 'loss';
    }

    function startDrag(civ: BoardPick, event: DragEvent) {
        if (civ.hidden) {
            event.preventDefault();
            return;
        }
        dragId = civ.id;
        event.dataTransfer?.setData('text/plain', civ.id);
        if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move';
    }

    function endDrag() {
        dragId = '';
        dropTarget = '';
    }

    function draggedCiv(event: DragEvent): BoardPick | undefined {
        const id = dragId || event.dataTransfer?.getData('text/plain') || '';
        return civById.get(id);
    }

    function allow(target: string, side: 'HOST' | 'GUEST', event: DragEvent) {
        const civ = draggedCiv(event);
        if (!civ || civ.hidden || civ.picker !== side) return;
        event.preventDefault();
        if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
        dropTarget = target;
    }

    function placeOnMap(mapPickId: string, side: 'HOST' | 'GUEST', slot: number, event: DragEvent) {
        event.preventDefault();
        const civ = draggedCiv(event);
        dropTarget = '';
        if (!civ || civ.hidden || civ.picker !== side || slot >= teamSize) return;
        const next = { ...placements };
        for (const [otherId, placed] of Object.entries(next)) {
            if (otherId === civ.id) continue;
            const parsed = parsePlacement(placed);
            if (parsed.mapId !== mapPickId || parsed.slot !== slot) continue;
            if (civById.get(otherId)?.picker === side) delete next[otherId];
        }
        next[civ.id] = formatPlacement(mapPickId, slot);
        persist(next, winners);
    }

    function returnToColumn(side: 'HOST' | 'GUEST', event: DragEvent) {
        event.preventDefault();
        const civ = draggedCiv(event);
        dropTarget = '';
        if (!civ || civ.picker !== side) return;
        if (placements[civ.id] === undefined) return;
        const next = { ...placements };
        delete next[civ.id];
        persist(next, winners);
    }

    function onCivError(event: Event, civ: BoardPick) {
        const img = event.currentTarget as HTMLImageElement;
        if (img.dataset.fallback === '1') return;
        img.dataset.fallback = '1';
        img.src = `https://backend.cdn.aoe2companion.com/public/aoe2/de/civilizations/${civ.optionId.toLowerCase()}.png`;
    }

    function onMapError(id: string) {
        brokenMaps = { ...brokenMaps, [id]: true };
    }
</script>

{#snippet civToken(civ: BoardPick)}
    {#if civ.hidden}
        <div class="civ-token grid place-items-center border border-surface-500 text-sm text-surface-300" title="Hidden">?</div>
    {:else}
        <div
            class="civ-token cursor-grab active:cursor-grabbing {civResult(civ) === 'win' ? `civ-win ${civ.picker.toLowerCase()}` : ''} {civResult(civ) === 'loss' ? 'civ-loss' : ''}"
            role="button"
            tabindex="0"
            draggable="true"
            title={civ.name}
            aria-label={civ.name}
            data-civ={civ.id}
            data-side={civ.picker}
            ondragstart={(event) => startDrag(civ, event)}
            ondragend={endDrag}
        >
            <img
                src={civ.imageUrl}
                alt=""
                onerror={(event) => onCivError(event, civ)}
            />
            <span class="civ-name">{civ.name}</span>
        </div>
    {/if}
{/snippet}

{#snippet civBan(civ: BoardPick, kind: 'civ' | 'map' = 'civ')}
    {@const label = civ.snipe ? `Sniped ${civ.name}` : `Banned ${civ.name}`}
    {#if civ.hidden}
        <div class="civ-ban grid place-items-center text-xs text-surface-300" class:is-snipe={civ.snipe} title={civ.snipe ? 'Hidden snipe' : 'Hidden ban'} data-ban={civ.id} data-kind={kind} data-snipe={civ.snipe ? '' : undefined}>
            ?
            {#if civ.snipe}<span class="snipe-mark">Snipe</span>{/if}
        </div>
    {:else if kind === 'map' && brokenMaps[civ.id]}
        <div class="civ-ban grid place-items-center px-1 text-center text-[0.5rem] text-surface-300" class:is-snipe={civ.snipe} title={label} aria-label={label} data-ban={civ.id} data-kind={kind} data-snipe={civ.snipe ? '' : undefined}>
            {#if civ.snipe}<span class="snipe-mark">Snipe</span>{/if}
            {civ.name}
        </div>
    {:else}
        <div class="civ-ban" class:is-snipe={civ.snipe} title={label} aria-label={label} data-ban={civ.id} data-kind={kind} data-snipe={civ.snipe ? '' : undefined}>
            <img
                src={civ.imageUrl}
                alt=""
                onerror={(event) => {
                    if (kind === 'map') onMapError(civ.id);
                    else onCivError(event, civ);
                }}
            />
            {#if civ.snipe}<span class="snipe-mark">Snipe</span>{/if}
            <span class="civ-name">{civ.name}</span>
        </div>
    {/if}
{/snippet}

{#snippet sideSlots(map: BoardPick, side: 'HOST' | 'GUEST')}
    <div class="flex flex-col items-center gap-1">
        <div class="flex flex-col items-center gap-1.5">
            {#each slotList as slot (slot)}
                {@const placed = placedCiv(map.id, side, slot)}
                <div
                    class="civ-slot grid place-items-center rounded-full border border-dashed {dropClass(side, map.id, slot)}"
                    role="group"
                    aria-label="{side === 'HOST' ? 'Host' : 'Guest'} {slot + 1} on {map.name}"
                    data-slot="{map.id}:{side}:{slot}"
                    ondragover={(event) => allow(`slot:${map.id}:${side}:${slot}`, side, event)}
                    ondrop={(event) => placeOnMap(map.id, side, slot, event)}
                >
                    {#if placed}
                        {@render civToken(placed)}
                    {/if}
                </div>
            {/each}
        </div>
        {#if hasSideCiv(map.id, side)}
            <button
                type="button"
                class="win-btn {side === 'HOST' ? 'host' : 'guest'}"
                class:is-on={winners[map.id] === side}
                aria-pressed={winners[map.id] === side}
                onclick={() => toggleWinner(map.id, side)}
            >Win</button>
        {/if}
    </div>
{/snippet}

{#snippet draftField(label: string, draft: WatchedDraft, value: string, onInput: (value: string) => void)}
    <label class="block text-left">
        <span class="mb-1 flex items-center justify-between gap-3 text-sm">
            <span>{label}</span>
            {#if draft.status !== 'idle'}
                <span class="text-xs {statusClass(draft.status)}" data-status={draft.status}>{statusLabel(draft.status)}</span>
            {/if}
        </span>
        <input
            class="w-full rounded-lg border border-surface-500 bg-surface-900 px-3 py-2"
            value={value}
            placeholder="id or aoe2cm link"
            spellcheck="false"
            autocapitalize="off"
            autocomplete="off"
            oninput={(event) => onInput((event.currentTarget as HTMLInputElement).value)}
        />
        {#if draft.state?.preset.name}
            <span class="mt-1 block truncate text-xs text-surface-400">{draft.state.preset.name}</span>
        {/if}
        {#if draft.error}
            <span class="mt-1 block text-xs text-red-300">{draft.error}</span>
        {/if}
    </label>
{/snippet}

<main class="mx-auto w-full max-w-5xl pb-16 text-left">
    <div class="mb-8 flex items-center justify-between">
        <a href={baseUrl} class="text-sm">Liga</a>
        <h1 class="m-0 text-2xl">Draft</h1>
        <span class="w-10"></span>
    </div>

    <form
        class="mx-auto grid max-w-3xl gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
        onsubmit={(event) => { event.preventDefault(); loadDrafts(); }}
    >
        {@render draftField('Map draft', mapDraft, mapInput, (value) => { mapInput = value; })}
        {@render draftField('Civ draft', civDraft, civInput, (value) => { civInput = value; })}
        <div class="flex flex-col items-end gap-2">
            <label class="block text-left text-sm">
                <span class="mb-1 block">Format</span>
                <select
                    class="format-select"
                    value={teamSize}
                    aria-label="Format"
                    title={teamSizeManual ? 'Format set by hand' : 'Guessed from the draft title'}
                    onchange={(event) => chooseTeamSize((event.currentTarget as HTMLSelectElement).value)}
                >
                    <option value={1}>1v1</option>
                    <option value={2}>2v2</option>
                    <option value={3}>3v3</option>
                    <option value={4}>4v4</option>
                </select>
            </label>
            <div class="flex gap-2">
                <button type="submit" class="load-btn">
                    {mapDraft.status === 'idle' && civDraft.status === 'idle' ? 'Load' : 'Reload'}
                </button>
                <button type="button" class="reset-btn" onclick={resetBoard}>Reset</button>
            </div>
        </div>
    </form>
    {#if inputError}
        <p class="mx-auto mt-2 max-w-3xl text-sm text-red-300">{inputError}</p>
    {/if}

    <p class="mx-auto mt-4 max-w-3xl text-center text-sm text-surface-400">
        Drag a civ onto a map to mark where it is played.
    </p>

    <section class="mx-auto mt-10 grid max-w-5xl grid-cols-[minmax(11rem,1fr)_auto_minmax(11rem,1fr)] items-stretch gap-x-4">
        <div class="flex h-full gap-3">
            {#if hostBans.length || hostMapOnly.length || hostSnipes.length}
                <div class="flex h-full flex-col" data-bans="HOST">
                    {#if hostBans.length}
                        <div class="ban-rail align-stack flex flex-col items-center gap-1.5" aria-label="{nameHost} civ bans">
                            <span class="rail-label">Bans</span>
                            {#each hostBans as civ (civ.id)}
                                {@render civBan(civ)}
                            {/each}
                        </div>
                    {/if}
                    {#if hostMapOnly.length || hostSnipes.length}
                        <div class="mt-auto flex flex-col gap-2">
                            {#if hostMapOnly.length}
                                <div class="ban-rail flex flex-col items-center gap-1.5" aria-label="{nameHost} map bans" data-map-bans="HOST">
                                    {#each hostMapOnly as map (map.id)}
                                        {@render civBan(map, 'map')}
                                    {/each}
                                </div>
                            {/if}
                            {#if hostSnipes.length}
                                <div class="ban-rail flex flex-col items-center gap-1.5" aria-label="{nameHost} snipes" data-snipes="HOST">
                                    <span class="rail-label">Snipes</span>
                                    {#each hostSnipes as map (map.id)}
                                        {@render civBan(map, 'map')}
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            {/if}
            <div class="flex h-full min-w-0 flex-1 flex-col">
            <div class="mb-3 flex items-center justify-center gap-2 text-lg">
                <span class="player-name host">{nameHost}</span>
                <!-- <span class="player-mark host" aria-hidden="true"></span> -->
            </div>
            <div
                class="flex min-h-48 flex-1 flex-col items-center gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:HOST' ? 'is-host-drop' : 'border-surface-700'}"
                role="group"
                aria-label="{nameHost} civs"
                data-column="HOST"
                ondragover={(event) => allow('col:HOST', 'HOST', event)}
                ondrop={(event) => returnToColumn('HOST', event)}
            >
                {#each hostStack as civ (civ.id)}
                    {@render civToken(civ)}
                {/each}
            </div>
            </div>
        </div>

        <div class="flex flex-col items-center gap-4">
            <div class="mb-3 flex items-center justify-center gap-3 text-lg font-semibold tabular-nums" data-score aria-label="{hostScore} to {guestScore}">
                <span class="host-score">{hostScore}</span>
                <span class="font-normal text-surface-500">–</span>
                <span class="guest-score">{guestScore}</span>
            </div>
            {#if orderedMaps.length === 0}
                <p class="w-48 text-center text-sm text-surface-400">Picked maps show up here.</p>
            {/if}
            {#each orderedMaps as map (map.id)}
                <div
                    class="matchup flex items-center gap-3"
                    class:won-host={winners[map.id] === 'HOST'}
                    class:won-guest={winners[map.id] === 'GUEST'}
                    data-map={map.id}
                    data-picker={map.picker}
                >
                    {@render sideSlots(map, 'HOST')}

                    <figure class="m-0">
                        {#if map.picker === 'NONE'}
                            <figcaption class="mb-1 text-center text-[0.65rem] uppercase tracking-widest text-slate-300">Admin</figcaption>
                        {/if}
                        <div class="map-disc picker-{map.picker.toLowerCase()}">
                            {#if map.hidden || brokenMaps[map.id] || !map.imageUrl}
                                <span class="grid h-full place-items-center px-2 text-center text-xs text-surface-300">{map.hidden ? '?' : map.name}</span>
                            {:else}
                                <img src={map.imageUrl} alt="" onerror={() => onMapError(map.id)} />
                            {/if}
                            <span class="map-name">{map.name}</span>
                        </div>
                    </figure>

                    {@render sideSlots(map, 'GUEST')}
                </div>
            {/each}
        </div>

        <div class="flex h-full gap-3">
            <div class="flex h-full min-w-0 flex-1 flex-col">
            <div class="mb-3 flex items-center justify-center gap-2 text-lg">
                <!-- <span class="player-mark guest" aria-hidden="true"></span> -->
                <span class="player-name guest">{nameGuest}</span>
            </div>
            <div
                class="flex min-h-48 flex-1 flex-col items-center gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:GUEST' ? 'is-guest-drop' : 'border-surface-700'}"
                role="group"
                aria-label="{nameGuest} civs"
                data-column="GUEST"
                ondragover={(event) => allow('col:GUEST', 'GUEST', event)}
                ondrop={(event) => returnToColumn('GUEST', event)}
            >
                {#each guestStack as civ (civ.id)}
                    {@render civToken(civ)}
                {/each}
            </div>
            </div>
            {#if guestBans.length || guestMapOnly.length || guestSnipes.length}
                <div class="flex h-full flex-col" data-bans="GUEST">
                    {#if guestBans.length}
                        <div class="ban-rail align-stack flex flex-col items-center gap-1.5" aria-label="{nameGuest} civ bans">
                            <span class="rail-label">Bans</span>
                            {#each guestBans as civ (civ.id)}
                                {@render civBan(civ)}
                            {/each}
                        </div>
                    {/if}
                    {#if guestMapOnly.length || guestSnipes.length}
                        <div class="mt-auto flex flex-col gap-2">
                            {#if guestMapOnly.length}
                                <div class="ban-rail flex flex-col items-center gap-1.5" aria-label="{nameGuest} map bans" data-map-bans="GUEST">
                                    {#each guestMapOnly as map (map.id)}
                                        {@render civBan(map, 'map')}
                                    {/each}
                                </div>
                            {/if}
                            {#if guestSnipes.length}
                                <div class="ban-rail flex flex-col items-center gap-1.5" aria-label="{nameGuest} snipes" data-snipes="GUEST">
                                    <span class="rail-label">Snipes</span>
                                    {#each guestSnipes as map (map.id)}
                                        {@render civBan(map, 'map')}
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            {/if}
        </div>
    </section>

    {#if adminBans.length || adminMapOnly.length || adminSnipes.length}
        <div class="ban-rail mx-auto mt-8 flex max-w-5xl flex-col items-center gap-2" data-bans="NONE">
            <div class="text-[0.65rem] uppercase tracking-widest text-slate-400">Admin</div>
            {#if adminBans.length}
                <div class="flex flex-col items-center gap-1.5">
                    <span class="rail-label">Bans</span>
                    <div class="flex flex-wrap justify-center gap-1.5">
                        {#each adminBans as civ (civ.id)}
                            {@render civBan(civ)}
                        {/each}
                    </div>
                </div>
            {/if}
            {#if adminMapOnly.length}
                <div class="flex flex-wrap justify-center gap-1.5" data-map-bans="NONE">
                    {#each adminMapOnly as map (map.id)}
                        {@render civBan(map, 'map')}
                    {/each}
                </div>
            {/if}
            {#if adminSnipes.length}
                <div class="flex flex-col items-center gap-1.5" data-snipes="NONE">
                    <span class="rail-label">Snipes</span>
                    <div class="flex flex-wrap justify-center gap-1.5">
                        {#each adminSnipes as map (map.id)}
                            {@render civBan(map, 'map')}
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</main>

<style>
    .load-btn {
        border-radius: 0.5rem;
        border: 0;
        background: rgb(56 189 248);
        color: rgb(15 23 42);
        font-weight: 600;
        padding: 0.55rem 1rem;
        cursor: pointer;
    }
    .load-btn:hover {
        background: rgb(125 211 252);
    }
    .reset-btn {
        border-radius: 0.5rem;
        border: 1px solid rgb(100 116 139);
        background: transparent;
        color: rgb(203 213 225);
        font-weight: 600;
        padding: 0.55rem 1rem;
        cursor: pointer;
    }
    .reset-btn:hover {
        border-color: rgb(203 213 225);
        color: white;
    }
    .format-select {
        border-radius: 0.5rem;
        border: 1px solid rgb(100 116 139);
        background: rgb(15 23 42);
        color: rgb(226 232 240);
        padding: 0.45rem 0.6rem;
    }
    .player-name {
        font-weight: 700;
        font-size: 1.25rem;
    }
    .player-name.host {
        color: rgb(0, 188, 212);
    }
    .player-name.guest {
        color: rgb(231 174 0);
    }
    .player-mark {
        width: 0.7rem;
        height: 0.7rem;
        flex: none;
        border-radius: 9999px;
    }
    .player-mark.host {
        background: rgb(0, 188, 212);
        /* background: rgb(56 189 248); */
    }
    .host-score {
        font-weight: 700;
        font-size: 1.75rem;
        color: rgb(203 213 225);
        /* color: rgb(56 189 248); */
    }
    .player-mark.guest {
        background: rgb(231, 174, 0);
        /* background: rgb(255 87 179); */
    }
    .guest-score {
        font-weight: 700;
        font-size: 1.75rem;
        color: rgb(203 213 225);
        /* color: rgb(255 87 179); */
    }
    .is-host-drop {
        border-color: rgb(0 188 212);
        background: rgb(0 188 212 / 0.1);
    }
    .is-guest-drop {
        border-color: rgb(231 174 0);
        background: rgb(231 174 0 / 0.1);
    }
    .win-btn {
        border-radius: 9999px;
        border: 1px solid rgb(100 116 139);
        background: transparent;
        color: rgb(203 213 225);
        font-size: 0.7rem;
        line-height: 1.2;
        padding: 0.15rem 0.55rem;
        cursor: pointer;
    }
    .win-btn.is-on.host {
        border-color: rgb(0 188 212);
        background: rgb(0 188 212);
        color: rgb(15 23 42);
        font-weight: 700;
    }
    .win-btn.is-on.guest {
        border-color: rgb(231 174 0);
        background: rgb(231 174 0);
        color: rgb(15 23 42);
        font-weight: 700;
    }
    .civ-token {
        position: relative;
        width: 5rem;
        height: 5rem;
        overflow: hidden;
        border-radius: 9999px;
    }
    .civ-token img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        pointer-events: none;
    }
    .civ-name {
        position: absolute;
        right: 0;
        bottom: 0;
        left: 0;
        overflow: hidden;
        padding: 0.05rem 0.2rem;
        font-size: 0.65rem;
        line-height: 1.2;
        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;
        background: rgb(15 23 42 / 0.72);
    }
    .rail-label {
        font-size: 0.6rem;
        line-height: 1;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgb(148 163 184);
    }
    .ban-rail {
        border: 1px solid rgb(127 29 29 / 0.55);
        border-radius: 1rem;
        padding: 0.45rem 0.4rem;
        background: rgb(15 23 42 / 0.45);
    }
    .ban-rail.align-stack {
        margin-top: 2.5rem;
    }
    .ban-rail[data-bans='NONE'] {
        margin-top: 2rem;
        padding: 0.55rem 0.7rem 0.65rem;
    }
    .civ-ban {
        position: relative;
        width: 2.75rem;
        height: 2.75rem;
        overflow: hidden;
        border-radius: 9999px;
        box-shadow: inset 0 0 0 2px rgb(127 29 29);
    }
    .civ-ban img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: grayscale(0.55);
    }
    .civ-ban .civ-name {
        font-size: 0.5rem;
        background: rgb(15 23 42 / 0.82);
    }
    .civ-ban.is-snipe {
        box-shadow: inset 0 0 0 2px rgb(120 53 15);
    }
    .snipe-mark {
        position: absolute;
        top: 0;
        right: 0;
        left: 0;
        z-index: 1;
        padding: 0.02rem 0.15rem;
        font-size: 0.45rem;
        line-height: 1.2;
        letter-spacing: 0.04em;
        text-align: center;
        text-transform: uppercase;
        color: rgb(254 215 170);
        background: rgb(15 23 42 / 0.82);
    }
    .civ-slot {
        width: 5rem;
        height: 5rem;
    }
    .civ-win.host {
        border-radius: 9999px;
        outline: 1px solid rgb(0 188 212);
        outline-offset: 1px;
    }
    .civ-win.guest {
        border-radius: 9999px;
        outline: 1px solid rgb(231 174 0);
        outline-offset: 1px;
    }
    .civ-loss {
        filter: grayscale(1);
        opacity: 0.4;
    }
    .matchup {
        border-radius: 1.25rem;
        padding: 0.4rem 0.45rem;
    }
    .matchup.won-host {
        background: rgb(0 188 212 / 0.08);
        box-shadow: inset 0 0 0 1px rgb(0 188 212 / 0.5);
    }
    .matchup.won-guest {
        background: rgb(231 174 0 / 0.08);
        box-shadow: inset 0 0 0 1px rgb(231 174 0 / 0.5);
    }
    .map-disc {
        position: relative;
        width: 6.5rem;
        height: 6.5rem;
        overflow: hidden;
        border-radius: 9999px;
        background: rgb(15 23 42);
    }
    .map-disc img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .picker-host {
        box-shadow: -5px 0 0 0 rgb(0 188 212);
    }
    .picker-guest {
        box-shadow: 5px 0 0 0 rgb(231 174 0);
    }
    .picker-none {
        box-shadow: 0 -5px 0 0 rgb(203 213 225);
    }
    h1 {
        font-size: 1.5rem;
        line-height: 1.2;
    }
    .map-name {
        position: absolute;
        right: 0;
        bottom: 0;
        left: 0;
        overflow: hidden;
        padding: 0.1rem 0.25rem;
        font-size: 0.7rem;
        text-align: center;
        text-overflow: ellipsis;
        white-space: nowrap;
        background: rgb(15 23 42 / 0.72);
    }
</style>
