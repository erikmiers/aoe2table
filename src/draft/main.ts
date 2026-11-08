import '../app.css'
import DraftApp from './DraftApp.svelte'
import { mount } from 'svelte'

const app = mount(DraftApp, {
    target: document.getElementById('app')!,
})

export default app
