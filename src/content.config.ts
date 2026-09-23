import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

const item = z.object({ title: z.string(), body: z.string() });

const landing = defineCollection({
	loader: glob({ pattern: '*.yaml', base: './src/content/landing' }),
	schema: z.object({
		hero: z.object({
			title: z.string(),
			lead: z.string(),
			download: z.string(),
			docs: z.string(),
			meta: z.string(),
			shotAlt: z.string(),
			shotCaption: z.string(),
		}),
		releases: z.object({
			toggle: z.string(),
			title: z.string(),
			latest: z.string(),
			prerelease: z.string(),
			all: z.string(),
		}),
		fixModel: z.object({
			title: z.string(),
			body: z.string(),
			points: z.array(z.string()).min(1),
			before: z.string(),
			after: z.string(),
			figureAlt: z.string(),
			figureCaption: z.string(),
		}),
		panels: z.object({
			title: z.string(),
			body: z.string(),
			items: z.object({
				quickAccess: z.string(),
				optimization: z.string(),
				customModel: z.string(),
				mmdOptions: z.string(),
				otherOptions: z.string(),
				visemes: z.string(),
				boneParenting: z.string(),
				modelScaling: z.string(),
				eyeTracking: z.string(),
				settings: z.string(),
			}),
		}),
		fork: z.object({
			title: z.string(),
			body: z.string(),
			timing: z.string(),
			before: z.string(),
			after: z.string(),
			items: z.array(item).length(4),
			more: z.string(),
		}),
		install: z.object({
			title: z.string(),
			download: item,
			disk: item,
			tab: item,
			note: z.string(),
		}),
		credits: z.object({
			title: z.string(),
			body: z.string(),
			source: z.string(),
			lineage: z.object({
				origin: z.string(),
				upstream: z.string(),
				fork: z.string(),
			}),
		}),
	}),
});

export const collections = {
	docs: defineCollection({
		loader: docsLoader(),
		schema: docsSchema({
			extend: z.object({ sourceUpdated: z.coerce.date().optional() }),
		}),
	}),
	landing,
};
