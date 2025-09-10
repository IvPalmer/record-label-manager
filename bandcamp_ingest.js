import Bandcamp from '@nutriot/bandcamp-api';
import dotenv from 'dotenv';
import { Client } from 'pg';

dotenv.config();

const api = new Bandcamp({ id: process.env.BANDCAMP_CLIENT_ID, secret: process.env.BANDCAMP_CLIENT_SECRET });
const bandId = Number(process.env.BAND_ID);

const pg = new Client({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: Number(process.env.POSTGRES_PORT || 5432),
  user: process.env.POSTGRES_USER || 'palmer',
  password: process.env.POSTGRES_PASSWORD || '',
  database: process.env.POSTGRES_DB || 'record_label_manager'
});

async function ensureTables() {
  await pg.query('CREATE SCHEMA IF NOT EXISTS raw');
  await pg.query(`CREATE TABLE IF NOT EXISTS raw.bandcamp_event_raw (
    id BIGSERIAL PRIMARY KEY,
    date_str text,
    occurred_at timestamp,
    item_name text,
    item_type text,
    artist text,
    quantity integer,
    currency text,
    item_total numeric(18,6),
    amount_received numeric(18,6),
    raw_row jsonb
  )`);
}

function mapRecord([id, details]) {
  const d = details || {};
  const dateStr = d.date || '';
  return {
    date_str: dateStr,
    occurred_at: new Date(dateStr),
    item_name: d.item_name || '',
    item_type: d.item_type || '',
    artist: d.artist || '',
    quantity: Number(d.quantity || 0),
    currency: d.currency || 'USD',
    item_total: Number(d.item_total || 0),
    amount_received: Number(d.amount_you_received || 0),
    raw_row: d
  };
}

async function insertBatch(rows) {
  if (!rows.length) return;
  const values = rows.map(r => `($$${r.date_str}$$, to_timestamp($$${new Date(r.occurred_at).toISOString()}$$, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'), $$${r.item_name}$$, $$${r.item_type}$$, $$${r.artist}$$, ${r.quantity}, $$${r.currency}$$, ${r.item_total}, ${r.amount_received}, $$${JSON.stringify(r.raw_row)}$$::jsonb)`).join(',');
  const sql = `INSERT INTO raw.bandcamp_event_raw (date_str, occurred_at, item_name, item_type, artist, quantity, currency, item_total, amount_received, raw_row) VALUES ${values}`;
  await pg.query(sql);
}

async function fetchChunk(start, end, accessToken) {
  const report = await api.getSalesReport(accessToken, { band_id: bandId, start_time: start, end_time: end });
  if (report && typeof report === 'object') {
    const rows = Object.entries(report).map(mapRecord);
    await insertBatch(rows);
    console.log(`Inserted ${rows.length} rows for ${start}..${end}`);
  } else {
    console.log(`No rows for ${start}..${end}`);
  }
}

(async () => {
  await pg.connect();
  await ensureTables();
  const creds = await api.getClientCredentials();
  if (!creds || !creds.ok) {
    console.error('Failed to get credentials', creds);
    process.exit(1);
  }
  let accessToken = creds.access_token;
  // Process a short window first (configurable via env)
  const start = process.env.BC_START || '2024-01-01';
  const end = process.env.BC_END || '2024-03-31';

  // split into monthly windows
  const startDate = new Date(start);
  const endDate = new Date(end);
  let cursor = new Date(startDate);
  while (cursor <= endDate) {
    const monthStart = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const monthEnd = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0);
    const s = monthStart.toISOString().slice(0, 10);
    const e = monthEnd.toISOString().slice(0, 10);
    await fetchChunk(s, e, accessToken);
    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  await pg.end();
  console.log('Done.');
})();
