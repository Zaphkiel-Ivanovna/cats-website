# Cats Blender Plugin website

Landing page and documentation for the [Cats Blender Plugin](https://github.com/Zaphkiel-Ivanovna/cats-blender-plugin-unofficial), built with Astro and Starlight, in English, French, German, Spanish, Italian and Polish.

## Commands

| Command        | Action                                              |
| -------------- | --------------------------------------------------- |
| `yarn install` | Install dependencies                                |
| `yarn dev`     | Start the dev server on `localhost:4321`            |
| `yarn build`   | Build the site to `./dist/`                         |
| `yarn preview` | Preview the build locally                           |
| `yarn check`   | Type-check pages and validate content               |
| `yarn format`  | Format the project with Prettier                    |
| `yarn icons`   | Regenerate the sidebar icon CSS from `src/icons.ts` |

## Deployment

### Cloudflare Workers

`wrangler.jsonc` deploys `dist/` as static assets (no Worker script). Headers live in `public/_headers`.

- Local check: `yarn preview:cf`, then deploy with `yarn deploy` (needs `wrangler login`).
- Workers Builds (Git integration): build command `yarn build`, deploy command `yarn wrangler deploy`, variable `YARN_VERSION=4.18.0`.
- Analytics: create a site in Cloudflare Web Analytics and set its token as `PUBLIC_CF_WEB_ANALYTICS_TOKEN` at build time.

### Vercel

`vercel.json` holds the build settings and headers. Vercel Web Analytics and Speed Insights load only on Vercel builds; enable both in the project.

### Environment variables

Listed in `.env.example`, all optional:

- `SITE_URL`: canonical URL, defaults to `https://cats.zaphkiel.dev`.
- `GITHUB_TOKEN`: raises the GitHub API limit for the releases menu at build time.
- `PUBLIC_CF_WEB_ANALYTICS_TOKEN`: Cloudflare Web Analytics site token.

Screenshots in `src/assets/screenshots/` are generated with `scripts/screenshots/run.py`.
