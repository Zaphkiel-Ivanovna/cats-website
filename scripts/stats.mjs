import { readFileSync } from 'node:fs';

const queries = JSON.parse(
	readFileSync(new URL('../observability/queries.json', import.meta.url), 'utf8'),
);

const token = process.env.CLOUDFLARE_API_TOKEN;
const account = process.env.CLOUDFLARE_ACCOUNT_ID;
const service = process.env.CLOUDFLARE_WORKER || 'cats-website';
const days = Math.min(
	Number(process.argv.find((arg) => arg.startsWith('--days='))?.split('=')[1] ?? 1),
	3,
);
const only = process.argv
	.find((arg) => arg.startsWith('--only='))
	?.split('=')[1]
	?.split(',');
const raw = process.argv.includes('--raw');

if (!token || !account) {
	console.error(
		'Set CLOUDFLARE_API_TOKEN (Workers Observability permission) and CLOUDFLARE_ACCOUNT_ID.',
	);
	process.exit(1);
}

const to = Date.now();
const from = to - days * 24 * 60 * 60 * 1000;

const api = `https://api.cloudflare.com/client/v4/accounts/${account}/workers/observability`;

async function call(path, method = 'GET', body) {
	const response = await fetch(`${api}${path}`, {
		method,
		headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
		body: body && JSON.stringify(body),
	});
	const json = await response.json();
	if (!response.ok || json.success === false) {
		throw new Error(
			json.errors?.map((error) => error.message).join('; ') || `HTTP ${response.status}`,
		);
	}
	return json.result;
}

function parameters(query) {
	return {
		datasets: ['cloudflare-workers'],
		filterCombination: 'and',
		filters: [
			{ key: '$metadata.service', operation: 'eq', type: 'string', value: service },
			...query.filters,
		],
		calculations: query.calculations,
		groupBys: query.groupBys ?? [],
		orderBy: query.orderBy,
		limit: query.limit ?? 100,
	};
}

function run(id, query, timeframe = { from, to }) {
	return call('/telemetry/query', 'POST', {
		queryId: `cats-${id}`,
		timeframe,
		view: 'calculations',
		limit: query.limit ?? 100,
		parameters: parameters(query),
	});
}

async function save() {
	const existing = await call('/queries');
	for (const query of Object.values(queries)) {
		const name = `Cats: ${query.title}`;
		const body = { name, description: query.description ?? '', parameters: parameters(query) };
		const match = existing.find((entry) => entry.name === name);
		if (match) await call(`/queries/${match.id}`, 'DELETE');
		await call('/queries', 'POST', body);
		console.log(`${match ? 'updated' : 'created'}  ${name}`);
	}
}

function rows(result) {
	const table = [];
	for (const calculation of result?.calculations ?? []) {
		for (const aggregate of calculation.aggregates ?? []) {
			const label = (aggregate.groups ?? []).map((group) => group.value).join(' / ') || 'total';
			let row = table.find((entry) => entry.label === label);
			if (!row) table.push((row = { label }));
			row[calculation.alias ?? calculation.calculation] = aggregate.value;
		}
	}
	return table;
}

function dayWindows() {
	const windows = [];
	const day = 24 * 60 * 60 * 1000;
	for (let start = Math.floor(from / day) * day; start < to; start += day) {
		windows.push({
			label: new Date(start).toISOString().slice(0, 10),
			timeframe: { from: Math.max(start, from), to: Math.min(start + day, to) },
		});
	}
	return windows;
}

async function perDay(id, query) {
	const table = [];
	for (const { label, timeframe } of dayWindows()) {
		const [total = { label }] = rows(await run(id, query, timeframe));
		table.push({ ...total, label });
	}
	return table;
}

if (process.argv.includes('--save')) {
	await save();
	process.exit(0);
}

console.log(`\n${service}, last ${days} day(s)\n`);
for (const [id, query] of Object.entries(queries)) {
	if (only && !only.includes(id)) continue;
	try {
		if (query.perDay && !raw) {
			console.log(`## ${query.title}`);
			console.table(await perDay(id, query));
			continue;
		}
		const result = await run(id, query);
		console.log(`## ${query.title}`);
		if (raw) {
			console.log(JSON.stringify(result, null, 2));
			continue;
		}
		const table = rows(result);
		if (table.length) console.table(table);
		else console.log('  no data\n');
	} catch (error) {
		console.log(`## ${query.title}\n  error: ${error.message}\n`);
	}
}
