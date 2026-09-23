import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pageIcons } from '../src/icons.ts';

const require = createRequire(import.meta.url);
const set = require('@iconify-json/ph/icons.json');

const svg = (name) => {
	const icon = set.icons[name] ?? set.icons[set.aliases?.[name]?.parent];
	if (!icon) throw new Error(`Unknown Phosphor icon: ${name}`);
	const size = icon.width ?? set.width ?? 256;
	return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}">${icon.body}</svg>`;
};

const rules = [...new Set(Object.values(pageIcons))].map((name) => {
	const uri = `url("data:image/svg+xml,${encodeURIComponent(svg(name))}")`;
	return `.sidebar-content a[data-icon='${name}']::before {\n\t-webkit-mask-image: ${uri};\n\tmask-image: ${uri};\n}`;
});

const out = new URL('../src/styles/icons.css', import.meta.url);
const base = readFileSync(new URL('./icons.base.css', import.meta.url), 'utf8');
writeFileSync(out, `${base}\n${rules.join('\n')}\n`);
console.log(`icons.css: ${rules.length} icons`);
