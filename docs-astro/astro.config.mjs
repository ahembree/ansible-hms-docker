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
			head: [
				{
					tag: 'meta',
					attrs: {
						property: 'og:title',
						content: 'HMS-Docker'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image',
						content: 'https://hmsdocker.dev/opengraph/hmsd_opengraph.png'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:logo',
						content: 'https://hmsdocker.dev/opengraph/hmsd_logo.png'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:type',
						content: 'website'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:url',
						content: 'https://hmsdocker.dev'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:description',
						content: 'An orchestrated Home Media Server deployment tool using Ansible and Docker'
					}
				},
			],
      social: [
				{ icon: 'discord', label: 'Discord', href: 'https://discord.gg/MqXTXvWSkZ' },
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/ahembree/ansible-hms-docker' },
				{ icon: 'document', label: 'Documentation', href: '//docs/intro' }
			],
      sidebar: [
				{
					label: 'Introduction',
					link: '/docs/intro'
				},
				{
					label: 'Container List',
					link: '/docs/container-list'
				},
				{
					label: 'Getting Started',
					autogenerate: { directory: '/docs/getting-started' },
				},
				{
					label: 'Examples',
					autogenerate: { directory: '/docs/examples' },
					collapsed: true
				},
				{
					label: 'Services and Integrations',
					autogenerate: { directory: '/docs/services' },
					collapsed: true
				},
				{
					label: 'Other',
					autogenerate: { directory: '/docs/other' },
					collapsed: true
				},
				{
					label: 'Release Notes',
					autogenerate: { directory: '/docs/release-notes' },
					collapsed: true
				},
      ],
			lastUpdated: true,
			editLink:{
				baseUrl: 'https://github.com/ahembree/ansible-hms-docker/edit/master/docs-astro'
			}
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
