import { join } from 'path';
import type { Config } from "tailwindcss";

import typography from '@tailwindcss/typography';
import { skeleton } from '@skeletonlabs/tw-plugin';


const config = {
	darkMode: 'class',
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		join(require.resolve(
			'@skeletonlabs/skeleton'),
			'../**/*.{html,js,svelte,ts}'
		)
	],
	theme: {
		extend: {},
	},
	plugins: [
        typography,
		skeleton({
            themes: {
				preset: [
					{
						name: 'wintry',
						enhancements: true,
					},
					{
						name: 'skeleton',
						enhancements: true,
					},
					{
						name: 'seafoam',
						enhancements: true,
					},
				],
			},
        })
	]
} satisfies Config;

export default config;

// export default {
//     content: ["./src/**/*.{html,js,svelte,ts}"],

//     theme: {
//         extend: {}
//     },

//     plugins: [require("@tailwindcss/typography")]
// } as Config;