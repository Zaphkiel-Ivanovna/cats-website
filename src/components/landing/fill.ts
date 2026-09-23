export function fill(template: string, vars: Record<string, string>): string {
	return template.replace(/\{(\w+)\}/g, (match, name: string) => vars[name] ?? match);
}
