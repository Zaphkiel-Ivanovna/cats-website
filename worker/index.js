const LOCALES = new Set(['fr', 'de', 'es', 'it', 'pl']);
const BOT_PATTERN =
	/bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|discord|telegram|whatsapp|curl|wget|python|headless|lighthouse/i;

function isPageView(request) {
	if (request.method !== 'GET') return false;
	const purpose = request.headers.get('Sec-Purpose') || request.headers.get('Purpose') || '';
	if (purpose.includes('prefetch') || purpose.includes('prerender')) return false;
	const dest = request.headers.get('Sec-Fetch-Dest');
	if (dest) return dest === 'document';
	return (request.headers.get('Accept') || '').includes('text/html');
}

function device(ua) {
	if (/ipad|tablet|kindle|silk/i.test(ua)) return 'tablet';
	if (/mobi|iphone|android/i.test(ua)) return 'mobile';
	return 'desktop';
}

function browser(ua) {
	if (/edg\//i.test(ua)) return 'Edge';
	if (/opr\/|opera/i.test(ua)) return 'Opera';
	if (/firefox|fxios/i.test(ua)) return 'Firefox';
	if (/chrome|crios/i.test(ua)) return 'Chrome';
	if (/safari/i.test(ua)) return 'Safari';
	return 'Other';
}

function os(ua) {
	if (/windows/i.test(ua)) return 'Windows';
	if (/iphone|ipad|ios/i.test(ua)) return 'iOS';
	if (/android/i.test(ua)) return 'Android';
	if (/mac os|macintosh/i.test(ua)) return 'macOS';
	if (/linux/i.test(ua)) return 'Linux';
	return 'Other';
}

function referrer(request, url) {
	const value = request.headers.get('Referer');
	if (!value) return 'direct';
	try {
		const host = new URL(value).hostname;
		return host === url.hostname ? 'internal' : host.replace(/^www\./, '');
	} catch {
		return 'unknown';
	}
}

async function visitorId(request, salt) {
	const ip = request.headers.get('CF-Connecting-IP') || '';
	const ua = request.headers.get('User-Agent') || '';
	const day = new Date().toISOString().slice(0, 10);
	const data = new TextEncoder().encode(`${salt}|${day}|${ip}|${ua}`);
	const digest = await crypto.subtle.digest('SHA-256', data);
	return [...new Uint8Array(digest).slice(0, 8)]
		.map((b) => b.toString(16).padStart(2, '0'))
		.join('');
}

export default {
	async fetch(request, env) {
		const response = await env.ASSETS.fetch(request);
		if (!isPageView(request)) return response;

		const url = new URL(request.url);
		const segments = url.pathname.split('/').filter(Boolean);
		const locale = LOCALES.has(segments[0]) ? segments[0] : 'en';
		const page = `/${(locale === 'en' ? segments : segments.slice(1)).join('/')}`;
		const ua = request.headers.get('User-Agent') || '';
		const cf = request.cf || {};

		console.log({
			event: 'pageview',
			path: url.pathname,
			page,
			locale,
			status: response.status,
			visitor: await visitorId(request, env.VISITOR_SALT || ''),
			country: cf.country || 'unknown',
			city: cf.city || 'unknown',
			referrer: referrer(request, url),
			utm_source: url.searchParams.get('utm_source') || '',
			device: device(ua),
			browser: browser(ua),
			os: os(ua),
			bot: BOT_PATTERN.test(ua),
			language:
				(request.headers.get('Accept-Language') || '').split(/[,;-]/)[0].toLowerCase() || 'unknown',
			host: url.hostname,
		});

		return response;
	},
};
