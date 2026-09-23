export const pageIcons: Record<string, string> = {
	'guides/install': 'download-simple',
	'guides/quick-start': 'path',
	'guides/troubleshooting': 'lifebuoy',
	'tools/quick-access': 'lightning',
	'tools/optimization': 'gauge',
	'tools/custom-model': 'puzzle-piece',
	'tools/mmd-options': 'magic-wand',
	'tools/other-options': 'sliders-horizontal',
	'tools/visemes': 'waveform',
	'tools/bone-parenting': 'tree-structure',
	'tools/model-scaling': 'arrows-out',
	'tools/eye-tracking': 'eye',
	'tools/settings': 'gear-six',
};

export const sidebarPage = (slug: string) => ({ slug, attrs: { 'data-icon': pageIcons[slug] } });
