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
        Head: './src/components/Head.astro',
      },
      title: 'HMS-Docker',
			description: 'Ansible playbook that deploys and configures a Docker-based home media server stack: Plex, Jellyfin, Sonarr, Radarr, Prowlarr, VPN, Traefik, and SSO.',
			logo: {
				src: './src/content/docs/static/img/logo.svg'
			},
			head: [
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
						property: 'og:image:width',
						content: '1200'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image:height',
						content: '600'
					}
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image:alt',
						content: 'HMS-Docker: an orchestrated Home Media Server deployment tool using Ansible and Docker'
					}
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:image',
						content: 'https://hmsdocker.dev/opengraph/hmsd_opengraph.png'
					}
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:image:alt',
						content: 'HMS-Docker: an orchestrated Home Media Server deployment tool using Ansible and Docker'
					}
				},
			],
      social: [
				{ icon: 'discord', label: 'Discord', href: 'https://discord.gg/MqXTXvWSkZ' },
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/ahembree/ansible-hms-docker' },
				{ icon: 'document', label: 'Documentation', href: '/docs/' }
			],
      sidebar: [
				{
					label: 'Introduction',
					link: '/docs/'
				},
				{
					label: 'Container List',
					link: '/docs/container-list'
				},
				{
					label: 'Getting Started',
					items: [{ autogenerate: { directory: '/docs/getting-started' } }],
				},
				{
					label: 'Examples',
					items: [{ autogenerate: { directory: '/docs/examples' } }],
					collapsed: true
				},
				{
					label: 'Services and Integrations',
					items: [{ autogenerate: { directory: '/docs/services' } }],
					collapsed: true
				},
				{
					label: 'Other',
					items: [{ autogenerate: { directory: '/docs/other' } }],
					collapsed: true
				},
				{
					label: 'Troubleshooting',
					items: [{ autogenerate: { directory: '/docs/troubleshooting' } }],
					collapsed: true
				},
				{
					label: 'Release Notes',
					items: [{ autogenerate: { directory: '/docs/release-notes' } }],
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
