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

Vercel builds the site with `vercel.json`. Optional environment variables are listed in `.env.example`:

- `GITHUB_TOKEN` raises the GitHub API limit when the releases menu is fetched at build time.
- `SITE_URL` sets the canonical URL; on Vercel it defaults to the production domain.

Vercel Web Analytics and Speed Insights are loaded on every page (`src/components/Footer.astro`); enable both in the Vercel project for data to be collected.

Screenshots in `src/assets/screenshots/` are generated with `scripts/screenshots/run.py`.
