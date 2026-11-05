// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeNext from 'starlight-theme-next'
import astroExpressiveCode from 'astro-expressive-code'

import tailwindcss from '@tailwindcss/vite';

import icon from 'astro-icon';
import sitemap from '@astrojs/sitemap';
import { slug as githubSlug } from 'github-slugger';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const SITE = 'https://hmsdocker.dev';
const DOCS_DIR = fileURLToPath(new URL('./src/content/docs/', import.meta.url));

/**
 * Map each docs page URL to the date of the newest git commit touching its source
 * file, so the sitemap can advertise an accurate <lastmod> per page. The URL is
 * derived the same way Astro's glob loader derives entry slugs (github-slugger per
 * path segment, trailing `/index` dropped). Returns an empty map without git history.
 */
function getDocsLastModified() {
	const lastModified = new Map();
	const log = spawnSync('git', ['log', '--format=t:%ct', '--name-only', '--relative', '--', '.'], {
		cwd: DOCS_DIR,
		encoding: 'utf-8',
		maxBuffer: 10 * 1024 * 1024,
	});
	if (log.error || log.status !== 0) return lastModified;

	let timestamp = 0;
	for (const line of log.stdout.split('\n')) {
		if (line.startsWith('t:')) {
			timestamp = Number(line.slice(2));
			continue;
		}
		if (!/\.mdx?$/.test(line)) continue;
		const slug = line
			.replace(/\.mdx?$/, '')
			.split('/')
			.map((segment) => githubSlug(segment))
			.join('/')
			.replace(/(^|\/)index$/, '');
		const url = new URL(slug ? `/${slug}/` : '/', SITE).href;
		// `git log` lists newest commits first, so the first date seen per file wins.
		if (!lastModified.has(url)) lastModified.set(url, new Date(timestamp * 1000));
	}
	return lastModified;
}

const docsLastModified = getDocsLastModified();

// https://astro.build/config
export default defineConfig({
	site: SITE,
  integrations: [
		// Registered explicitly (instead of Starlight's built-in default) to add <lastmod>.
		sitemap({
			serialize(item) {
				const lastmod = docsLastModified.get(item.url);
				if (lastmod) item.lastmod = lastmod.toISOString();
				return item;
			},
		}),
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
					tag: 'link',
					attrs: { rel: 'icon', type: 'image/png', sizes: '96x96', href: '/favicon-96x96.png' }
				},
				{
					tag: 'link',
					attrs: { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/icon-192.png' }
				},
				{
					tag: 'link',
					attrs: { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' }
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
					link: '/docs/container-list/'
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
