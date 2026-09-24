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

async function run(id, query) {
	const body = {
		queryId: `cats-${id}`,
		timeframe: { from, to },
		view: 'calculations',
		chart: Boolean(query.timeseries),
		granularity: query.granularity,
		limit: query.limit ?? 100,
		parameters: {
			datasets: ['cloudflare-workers'],
			filterCombination: 'and',
			filters: [
				{
					kind: 'filter',
					key: '$metadata.service',
					operation: 'eq',
					type: 'string',
					value: service,
				},
				...query.filters.map((filter) => ({ kind: 'filter', ...filter })),
			],
			calculations: query.calculations.map((calc) => ({ key: null, keyType: null, ...calc })),
			groupBys: query.groupBys ?? [],
			orderBy: query.orderBy,
			limit: query.limit ?? 100,
		},
	};
	const response = await fetch(
		`https://api.cloudflare.com/client/v4/accounts/${account}/workers/observability/telemetry/query`,
		{
			method: 'POST',
			headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
			body: JSON.stringify(body),
		},
	);
	const json = await response.json();
	if (!response.ok || json.success === false) {
		throw new Error(
			json.errors?.map((error) => error.message).join('; ') || `HTTP ${response.status}`,
		);
	}
	return json.result;
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

console.log(`\n${service}, last ${days} day(s)\n`);
for (const [id, query] of Object.entries(queries)) {
	if (only && !only.includes(id)) continue;
	try {
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
