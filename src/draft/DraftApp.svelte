<script lang="ts">
    import { bannedCivs, pickedCivs, pickedMaps, boardKey, readBoard, writeBoard, prunePlacements, pruneWinners, type BoardPick, type WinnerSide } from './board';
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
    let civById = $derived(new Map(civs.map((civ) => [civ.id, civ])));
    let nameHost = $derived(mapDraft.state?.nameHost || civDraft.state?.nameHost || 'Host');
    let nameGuest = $derived(mapDraft.state?.nameGuest || civDraft.state?.nameGuest || 'Guest');
    let hostStack = $derived(civs.filter((civ) => civ.picker === 'HOST' && placements[civ.id] === undefined));
    let guestStack = $derived(civs.filter((civ) => civ.picker === 'GUEST' && placements[civ.id] === undefined));
    let hostBans = $derived(bans.filter((civ) => civ.picker === 'HOST'));
    let guestBans = $derived(bans.filter((civ) => civ.picker === 'GUEST'));
    let adminBans = $derived(bans.filter((civ) => civ.picker === 'NONE'));

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
    });

    $effect(() => {
        if ((loadedMapId && !ready(mapDraft)) || (loadedCivId && !ready(civDraft))) return;
        const mapIds = new Set(maps.map((map) => map.id));
        const civIds = new Set(civs.map((civ) => civ.id));
        const nextPlacements = prunePlacements(placements, mapIds, civIds);
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

    function placedCiv(mapPickId: string, side: 'HOST' | 'GUEST'): BoardPick | undefined {
        for (const [civPickId, placedMap] of Object.entries(placements)) {
            if (placedMap !== mapPickId) continue;
            const civ = civById.get(civPickId);
            if (civ?.picker === side) return civ;
        }
        return undefined;
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
        });
    }

    function toggleWinner(mapPickId: string, side: WinnerSide) {
        const next = { ...winners };
        if (next[mapPickId] === side) delete next[mapPickId];
        else next[mapPickId] = side;
        persist(placements, next);
    }

    function civResult(civ: BoardPick): 'win' | 'loss' | '' {
        const mapPickId = placements[civ.id];
        if (!mapPickId) return '';
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

    function placeOnMap(mapPickId: string, side: 'HOST' | 'GUEST', event: DragEvent) {
        event.preventDefault();
        const civ = draggedCiv(event);
        dropTarget = '';
        if (!civ || civ.hidden || civ.picker !== side) return;
        const next = { ...placements };
        for (const [otherId, placedMap] of Object.entries(next)) {
            if (otherId === civ.id || placedMap !== mapPickId) continue;
            if (civById.get(otherId)?.picker === side) delete next[otherId];
        }
        next[civ.id] = mapPickId;
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
            class="civ-token cursor-grab active:cursor-grabbing {civResult(civ) === 'win' ? 'civ-win' : ''} {civResult(civ) === 'loss' ? 'civ-loss' : ''}"
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

{#snippet civBan(civ: BoardPick)}
    {#if civ.hidden}
        <div class="civ-ban grid place-items-center text-xs text-surface-300" title="Hidden ban" data-ban={civ.id}>?</div>
    {:else}
        <div class="civ-ban" title="Banned: {civ.name}" aria-label="Banned {civ.name}" data-ban={civ.id}>
            <img src={civ.imageUrl} alt="" onerror={(event) => onCivError(event, civ)} />
            <span class="civ-name">{civ.name}</span>
        </div>
    {/if}
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
        <button type="submit" class="load-btn">
            {mapDraft.status === 'idle' && civDraft.status === 'idle' ? 'Load' : 'Reload'}
        </button>
    </form>
    {#if inputError}
        <p class="mx-auto mt-2 max-w-3xl text-sm text-red-300">{inputError}</p>
    {/if}

    <p class="mx-auto mt-4 max-w-3xl text-center text-sm text-surface-400">
        Drag a civ onto a map to mark where it is played.
    </p>

    <section class="mx-auto mt-10 grid max-w-5xl grid-cols-[minmax(11rem,1fr)_auto_minmax(11rem,1fr)] items-stretch gap-x-4">
        <div class="flex h-full gap-3">
            {#if hostBans.length}
                <div class="ban-rail flex flex-col items-center gap-1.5 self-start" aria-label="{nameHost} bans" data-bans="HOST">
                    {#each hostBans as civ (civ.id)}
                        {@render civBan(civ)}
                    {/each}
                </div>
            {/if}
            <div class="flex h-full min-w-0 flex-1 flex-col">
            <div class="mb-3 text-center text-lg">{nameHost}</div>
            <div
                class="flex min-h-48 flex-1 flex-col items-center gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:HOST' ? 'border-sky-400 bg-sky-400/10' : 'border-surface-700'}"
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

        <div class="flex flex-col items-center gap-4 pt-10">
            {#if maps.length === 0}
                <p class="w-48 text-center text-sm text-surface-400">Picked maps show up here.</p>
            {/if}
            {#each maps as map (map.id)}
                {@const hostPlaced = placedCiv(map.id, 'HOST')}
                {@const guestPlaced = placedCiv(map.id, 'GUEST')}
                <div
                    class="matchup flex items-center gap-3"
                    class:is-done={winners[map.id] != null}
                    data-map={map.id}
                    data-picker={map.picker}
                >
                    <div class="flex flex-col items-center gap-1">
                    <div
                        class="civ-slot grid place-items-center rounded-full border border-dashed {dropTarget === `slot:${map.id}:HOST` ? 'border-sky-400 bg-sky-400/10' : 'border-surface-600'}"
                        role="group"
                        aria-label="Host on {map.name}"
                        data-slot="{map.id}:HOST"
                        ondragover={(event) => allow(`slot:${map.id}:HOST`, 'HOST', event)}
                        ondrop={(event) => placeOnMap(map.id, 'HOST', event)}
                    >
                        {#if hostPlaced}
                            {@render civToken(hostPlaced)}
                        {/if}
                    </div>
                    {#if hostPlaced}
                    <button
                        type="button"
                        class="win-btn"
                        class:is-on={winners[map.id] === 'HOST'}
                        aria-pressed={winners[map.id] === 'HOST'}
                        onclick={() => toggleWinner(map.id, 'HOST')}
                    >Win</button>
                    {/if}
                    </div>

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

                    <div class="flex flex-col items-center gap-1">
                    <div
                        class="civ-slot grid place-items-center rounded-full border border-dashed {dropTarget === `slot:${map.id}:GUEST` ? 'border-amber-300 bg-amber-300/10' : 'border-surface-600'}"
                        role="group"
                        aria-label="Guest on {map.name}"
                        data-slot="{map.id}:GUEST"
                        ondragover={(event) => allow(`slot:${map.id}:GUEST`, 'GUEST', event)}
                        ondrop={(event) => placeOnMap(map.id, 'GUEST', event)}
                    >
                        {#if guestPlaced}
                            {@render civToken(guestPlaced)}
                        {/if}
                    </div>
                    {#if guestPlaced}
                    <button
                        type="button"
                        class="win-btn"
                        class:is-on={winners[map.id] === 'GUEST'}
                        aria-pressed={winners[map.id] === 'GUEST'}
                        onclick={() => toggleWinner(map.id, 'GUEST')}
                    >Win</button>
                    {/if}
                    </div>
                </div>
            {/each}
        </div>

        <div class="flex h-full gap-3">
            <div class="flex h-full min-w-0 flex-1 flex-col">
            <div class="mb-3 text-center text-lg">{nameGuest}</div>
            <div
                class="flex min-h-48 flex-1 flex-col items-center gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:GUEST' ? 'border-amber-300 bg-amber-300/10' : 'border-surface-700'}"
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
            {#if guestBans.length}
                <div class="ban-rail flex flex-col items-center gap-1.5 self-start" aria-label="{nameGuest} bans" data-bans="GUEST">
                    {#each guestBans as civ (civ.id)}
                        {@render civBan(civ)}
                    {/each}
                </div>
            {/if}
        </div>
    </section>

    {#if adminBans.length}
        <div class="ban-rail mx-auto mt-8 flex max-w-5xl flex-col items-center gap-2" data-bans="NONE">
            <div class="text-[0.65rem] uppercase tracking-widest text-slate-400">Admin</div>
            <div class="flex flex-wrap justify-center gap-1.5">
                {#each adminBans as civ (civ.id)}
                    {@render civBan(civ)}
                {/each}
            </div>
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
    .win-btn.is-on {
        border-color: rgb(250 204 21);
        background: rgb(250 204 21);
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
    .ban-rail {
        margin-top: 2.5rem;
        border: 1px solid rgb(127 29 29 / 0.55);
        border-radius: 1rem;
        padding: 0.45rem 0.4rem;
        background: rgb(15 23 42 / 0.45);
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
    .civ-slot {
        width: 5rem;
        height: 5rem;
    }
    .civ-win {
        border-radius: 9999px;
        outline: 3px solid rgb(250 204 21);
        outline-offset: 2px;
    }
    .civ-loss {
        filter: grayscale(1);
        opacity: 0.4;
    }
    .matchup {
        border-radius: 1.25rem;
        padding: 0.4rem 0.45rem;
    }
    .matchup.is-done {
        background: rgb(250 204 21 / 0.08);
        box-shadow: inset 0 0 0 1px rgb(250 204 21 / 0.5);
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
        box-shadow: -5px 0 0 0 rgb(56 189 248);
    }
    .picker-guest {
        box-shadow: 5px 0 0 0 rgb(251 191 36);
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
