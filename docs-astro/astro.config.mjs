// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeNext from 'starlight-theme-next'
import astroExpressiveCode from 'astro-expressive-code'

import tailwindcss from '@tailwindcss/vite';

import icon from 'astro-icon';

// https://astro.build/config
export default defineConfig({
	site: 'https://hmsdocker.dev',
  integrations: [
		astroExpressiveCode({
      themes: ['github-dark-default'],
    }),
		starlight({
			favicon: 'favicon.ico',
      plugins: [starlightThemeNext()],
			customCss: [
				'./src/styles/global.css',
				'./src/styles/landing.css'
			],
			components: {
        ThemeProvider: './src/components/ForceDarkTheme.astro',
        ThemeSelect: './src/components/EmptyThemeSelect.astro',
      },
      title: 'HMS-Docker',
			logo: {
				src: './src/assets/hmsd_logo.png'
			},
      social: [
				{ icon: 'discord', label: 'Discord', href: 'https://discord.gg/MqXTXvWSkZ' },
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/ahembree/ansible-hms-docker' },
				{ icon: 'document', label: 'Documentation', href: '/intro' }
			],
      sidebar: [
				{
					label: 'Introduction',
					link: 'intro'
				},
				{
					label: 'Container List',
					link: 'container-list'
				},
				{
					label: 'Getting Started',
					autogenerate: { directory: 'getting-started' },
				},
				{
					label: 'Examples',
					autogenerate: { directory: 'examples' },
					collapsed: true
				},
				{
					label: 'Services and Integrations',
					autogenerate: { directory: 'services' },
					collapsed: true
				},
				{
					label: 'Other',
					autogenerate: { directory: 'other' },
					collapsed: true
				},
				{
					label: 'Release Notes',
					autogenerate: { directory: 'release-notes' },
					collapsed: true
				},
      ],
		}),
		icon({
			include: {
				mdi: [
					'format-list-bulleted',
					'refresh-auto',
					'shield-lock',
					'cog-transfer-outline',
					'nas',
					'account-lock',
					'video-4k-box',
					'lock',
					'home',
					'script'
				],
				tabler: [
					'brand-cloudflare',
					'cog-transfer-outline'
				],
				lucide: [
					'gpu'
				]
			}
		})
	],

  vite: {
    plugins: [
			tailwindcss()
		],
  },
});
