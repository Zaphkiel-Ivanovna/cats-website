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

`wrangler.jsonc` deploys `dist/` as static assets. A pass-through Worker (`worker/index.js`) runs on page requests only, so Workers Logs record every page view; `/_astro/*` and `/pagefind/*` are served straight from the asset store. Headers live in `public/_headers`.

- Local check: `yarn preview:cf`, then deploy with `yarn deploy` (needs `wrangler login`).
- Workers Builds (Git integration): build command `yarn build`, deploy command `yarn wrangler deploy`, variable `YARN_VERSION=4.18.0`.
- Analytics: create a site in Cloudflare Web Analytics and set its token as `PUBLIC_CF_WEB_ANALYTICS_TOKEN` at build time.

### Observability

The Worker logs one structured `pageview` event per real page visit (prefetches and assets are skipped): `page`, `locale`, `status`, `country`, `city`, `referrer`, `utm_source`, `device`, `browser`, `os`, `language`, `bot`, and `visitor`, a daily-rotating anonymous hash of IP and user agent salted with the `VISITOR_SALT` secret. No IP address is stored.

- Terminal report: `yarn stats` (`--days=1` to `3`, `--only=pages,countries`, `--raw`). Needs `CLOUDFLARE_API_TOKEN` with the Workers Observability permission and `CLOUDFLARE_ACCOUNT_ID`, from `.env` or the environment.
- Query definitions: `observability/queries.json` (visitors, page views, daily trend, pages, locales, countries, referrers, UTM campaigns, devices, browsers, systems, browser languages, 404s, bots).
- Dashboard: Workers & Pages › cats-website › Observability › Query Builder. Filter `event = pageview` and `bot = false`, then use Count Distinct on `visitor` for unique visitors and Count for page views, grouped by any field above.

Free plan: 200,000 log events per day, kept 3 days.

### Vercel

`vercel.json` holds the build settings and headers. Vercel Web Analytics and Speed Insights load only on Vercel builds; enable both in the project.

### Environment variables

Listed in `.env.example`, all optional:

- `SITE_URL`: canonical URL, defaults to `https://cats-plugin.zaphkiel.dev`.
- `GITHUB_TOKEN`: raises the GitHub API limit for the releases menu at build time.
- `PUBLIC_CF_WEB_ANALYTICS_TOKEN`: Cloudflare Web Analytics site token.

Screenshots in `src/assets/screenshots/` are generated with `scripts/screenshots/run.py`.
