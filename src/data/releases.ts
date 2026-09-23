import addon from './addon.json';

export interface Release {
	version: string;
	date: string;
	url: string;
	size: number | null;
	prerelease: boolean;
	latest: boolean;
}

interface GitHubAsset {
	name: string;
	size: number;
	browser_download_url: string;
}

interface GitHubRelease {
	tag_name: string;
	draft: boolean;
	prerelease: boolean;
	published_at: string;
	assets: GitHubAsset[];
}

const repo = new URL(addon.repoUrl).pathname.replace(/^\/|\/$/g, '');

const fallback: Release[] = [
	{
		version: addon.version,
		date: addon.releaseDate,
		url: addon.downloadUrl,
		size: null,
		prerelease: false,
		latest: true,
	},
];

async function load(): Promise<Release[]> {
	const headers: Record<string, string> = {
		Accept: 'application/vnd.github+json',
		'User-Agent': 'cats-website',
	};
	const token = process.env.GITHUB_TOKEN;
	if (token) headers.Authorization = `Bearer ${token}`;

	try {
		const response = await fetch(`https://api.github.com/repos/${repo}/releases?per_page=50`, {
			headers,
		});
		if (!response.ok) throw new Error(`GitHub API answered ${response.status}`);
		const data = (await response.json()) as GitHubRelease[];
		const releases = data
			.filter((release) => !release.draft)
			.flatMap((release) => {
				const zip = release.assets.find((asset) => asset.name.endsWith('.zip'));
				if (!zip) return [];
				return [
					{
						version: release.tag_name,
						date: release.published_at,
						url: zip.browser_download_url,
						size: zip.size,
						prerelease: release.prerelease,
						latest: false,
					},
				];
			});
		const latest = releases.find((release) => !release.prerelease);
		if (latest) latest.latest = true;
		if (releases.length) return releases;
	} catch (error) {
		console.warn(`[releases] Falling back to addon.json: ${(error as Error).message}`);
	}
	return fallback;
}

export const releases = await load();
export const releasesUrl = `${addon.repoUrl}/releases`;
