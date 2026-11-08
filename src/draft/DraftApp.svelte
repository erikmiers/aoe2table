<script lang="ts">
    import { pickedCivs, pickedMaps, boardKey, readPlacements, writePlacements, prunePlacements, type BoardPick, type Side } from './board';
    import { watchDraft } from './liveDraft';
    import { emptyWatched, parseDraftId, type DraftStatus, type WatchedDraft } from './types';

    const baseUrl = import.meta.env.BASE_URL;

    function queryValue(key: string): string {
        if (typeof location === 'undefined') return '';
        return new URLSearchParams(location.search).get(key) ?? '';
    }

    let mapInput = $state(queryValue('maps'));
    let civInput = $state(queryValue('civs'));
    let mapDraft = $state<WatchedDraft>(emptyWatched());
    let civDraft = $state<WatchedDraft>(emptyWatched());
    let placements = $state<Record<string, string>>({});
    let dragId = $state('');
    let dropTarget = $state('');
    let brokenMaps = $state<Record<string, boolean>>({});

    let mapId = $derived(parseDraftId(mapInput));
    let civId = $derived(parseDraftId(civInput));
    let maps = $derived(pickedMaps(mapDraft.state));
    let civs = $derived(pickedCivs(civDraft.state));
    let civById = $derived(new Map(civs.map((civ) => [civ.id, civ])));
    let nameHost = $derived(mapDraft.state?.nameHost || civDraft.state?.nameHost || 'Host');
    let nameGuest = $derived(mapDraft.state?.nameGuest || civDraft.state?.nameGuest || 'Guest');
    let hostStack = $derived(civs.filter((civ) => civ.picker === 'HOST' && placements[civ.id] === undefined));
    let guestStack = $derived(civs.filter((civ) => civ.picker === 'GUEST' && placements[civ.id] === undefined));

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
        const id = mapId;
        let disconnect = () => {};
        if (!id) {
            mapDraft = emptyWatched();
            return;
        }
        mapDraft = { id, status: 'connecting', state: null, error: null };
        const timer = window.setTimeout(() => {
            disconnect = watchDraft(id, (draft) => {
                mapDraft = draft;
            });
        }, 400);
        return () => {
            window.clearTimeout(timer);
            disconnect();
        };
    });

    $effect(() => {
        const id = civId;
        let disconnect = () => {};
        if (!id) {
            civDraft = emptyWatched();
            return;
        }
        civDraft = { id, status: 'connecting', state: null, error: null };
        const timer = window.setTimeout(() => {
            disconnect = watchDraft(id, (draft) => {
                civDraft = draft;
            });
        }, 400);
        return () => {
            window.clearTimeout(timer);
            disconnect();
        };
    });

    $effect(() => {
        const key = boardKey(mapId, civId);
        if (key === loadedKey) return;
        loadedKey = key;
        placements = readPlacements(key);
    });

    $effect(() => {
        if (!ready(mapDraft) || !ready(civDraft)) return;
        const next = prunePlacements(
            placements,
            new Set(maps.map((map) => map.id)),
            new Set(civs.map((civ) => civ.id)),
        );
        if (next !== placements) {
            placements = next;
            writePlacements(boardKey(mapId, civId), next);
        }
    });

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

    function rowClass(picker: Side): string {
        if (picker === 'HOST') return 'pick-host';
        if (picker === 'GUEST') return 'pick-guest';
        return '';
    }

    function placedCiv(mapPickId: string, side: 'HOST' | 'GUEST'): BoardPick | undefined {
        for (const [civPickId, placedMap] of Object.entries(placements)) {
            if (placedMap !== mapPickId) continue;
            const civ = civById.get(civPickId);
            if (civ?.picker === side) return civ;
        }
        return undefined;
    }

    function save(next: Record<string, string>) {
        placements = next;
        writePlacements(boardKey(mapId, civId), next);
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
        save(next);
    }

    function returnToColumn(side: 'HOST' | 'GUEST', event: DragEvent) {
        event.preventDefault();
        const civ = draggedCiv(event);
        dropTarget = '';
        if (!civ || civ.picker !== side) return;
        if (placements[civ.id] === undefined) return;
        const next = { ...placements };
        delete next[civ.id];
        save(next);
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
        <div class="grid size-12 place-items-center rounded-full border border-surface-500 text-sm text-surface-300" title="Hidden">?</div>
    {:else}
        <div
            class="size-12 cursor-grab active:cursor-grabbing"
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
                class="pointer-events-none size-12 rounded-full"
                src={civ.imageUrl}
                alt={civ.name}
                onerror={(event) => onCivError(event, civ)}
            />
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

    <div class="mx-auto grid max-w-3xl gap-4 sm:grid-cols-2">
        {@render draftField('Map draft', mapDraft, mapInput, (value) => { mapInput = value; })}
        {@render draftField('Civ draft', civDraft, civInput, (value) => { civInput = value; })}
    </div>

    <p class="mx-auto mt-4 max-w-3xl text-center text-sm text-surface-400">
        Drag a civ onto a map to mark where it is played.
    </p>

    <section class="mx-auto mt-10 grid max-w-3xl grid-cols-[minmax(7rem,1fr)_auto_minmax(7rem,1fr)] items-start gap-x-4">
        <div>
            <div class="mb-3 text-right text-lg">{nameHost}</div>
            <div
                class="flex min-h-48 flex-col items-end gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:HOST' ? 'border-sky-400 bg-sky-400/10' : 'border-surface-700'}"
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

        <div class="flex flex-col items-center gap-4 pt-10">
            {#if maps.length === 0}
                <p class="w-48 text-center text-sm text-surface-400">Picked maps show up here.</p>
            {/if}
            {#each maps as map (map.id)}
                {@const hostPlaced = placedCiv(map.id, 'HOST')}
                {@const guestPlaced = placedCiv(map.id, 'GUEST')}
                <div class="flex items-center gap-3 {rowClass(map.picker)}" data-map={map.id} data-picker={map.picker}>
                    <div
                        class="grid size-14 place-items-center rounded-full border border-dashed {dropTarget === `slot:${map.id}:HOST` ? 'border-sky-400 bg-sky-400/10' : 'border-surface-600'}"
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

                    <div
                        class="grid size-14 place-items-center rounded-full border border-dashed {dropTarget === `slot:${map.id}:GUEST` ? 'border-amber-300 bg-amber-300/10' : 'border-surface-600'}"
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
                </div>
            {/each}
        </div>

        <div>
            <div class="mb-3 text-lg">{nameGuest}</div>
            <div
                class="flex min-h-48 flex-col items-start gap-3 rounded-2xl border border-dashed px-3 py-3 {dropTarget === 'col:GUEST' ? 'border-amber-300 bg-amber-300/10' : 'border-surface-700'}"
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
    </section>
</main>

<style>
    .pick-host {
        transform: translateX(-1.25rem);
    }
    .pick-guest {
        transform: translateX(1.25rem);
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
