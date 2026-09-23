export function siteUrl(...candidates: (string | undefined)[]): string | undefined {
	for (const value of candidates) {
		const raw = value?.trim();
		if (!raw) continue;
		try {
			return new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`).href;
		} catch {
			console.warn(`[site] Ignoring invalid site URL: ${raw}`);
		}
	}
	return undefined;
}
