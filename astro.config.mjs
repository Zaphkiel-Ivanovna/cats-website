// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import icon from 'astro-icon';
import { sidebarPage } from './src/icons.ts';
import { siteUrl } from './src/site.ts';

const site = siteUrl(
	process.env.SITE_URL,
	process.env.VERCEL_PROJECT_PRODUCTION_URL,
	'https://cats-plugin.zaphkiel.dev',
);

export default defineConfig({
	site,
	integrations: [
		starlight({
			title: 'Cats Blender Plugin',
			logo: { src: './src/assets/cats-mark.svg' },
			customCss: ['./src/styles/theme.css', './src/styles/docs.css', './src/styles/icons.css'],
			expressiveCode: {
				styleOverrides: {
					borderRadius: '8px',
					borderColor: 'var(--sl-color-gray-5)',
					codeBackground: 'var(--sl-color-gray-6)',
					frames: {
						frameBoxShadowCssValue: 'none',
						editorTabBarBackground: 'var(--sl-color-black)',
						editorActiveTabIndicatorTopColor: 'var(--sl-color-accent)',
						terminalTitlebarBackground: 'var(--sl-color-black)',
						terminalTitlebarBorderBottomColor: 'var(--sl-color-gray-5)',
					},
				},
			},
			components: {
				Hero: './src/components/Hero.astro',
				PageTitle: './src/components/PageTitle.astro',
				Footer: './src/components/Footer.astro',
			},
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/Zaphkiel-Ivanovna/cats-blender-plugin-unofficial',
				},
			],
			defaultLocale: 'root',
			locales: {
				root: { label: 'English', lang: 'en' },
				fr: { label: 'Français', lang: 'fr' },
				de: { label: 'Deutsch', lang: 'de' },
				es: { label: 'Español', lang: 'es' },
				it: { label: 'Italiano', lang: 'it' },
				pl: { label: 'Polski', lang: 'pl' },
			},
			sidebar: [
				{
					label: 'Getting started',
					translations: {
						fr: 'Premiers pas',
						de: 'Erste Schritte',
						es: 'Primeros pasos',
						it: 'Per iniziare',
						pl: 'Pierwsze kroki',
					},
					items: ['guides/install', 'guides/quick-start', 'guides/troubleshooting'].map(
						sidebarPage,
					),
				},
				{
					label: 'Tools',
					translations: {
						fr: 'Outils',
						de: 'Werkzeuge',
						es: 'Herramientas',
						it: 'Strumenti',
						pl: 'Narzędzia',
					},
					items: [
						'tools/quick-access',
						'tools/optimization',
						'tools/custom-model',
						'tools/mmd-options',
						'tools/other-options',
						'tools/visemes',
						'tools/bone-parenting',
						'tools/model-scaling',
						'tools/eye-tracking',
						'tools/settings',
					].map(sidebarPage),
				},
			],
		}),
		icon(),
	],
});
