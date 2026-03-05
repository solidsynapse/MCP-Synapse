from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

raw = Path('tmp.usage.recent.after_seed.utf8.json').read_text(encoding='utf-8-sig')
outer = json.loads(raw)
payload = json.loads(outer.get('text') or '{}')
rows = list(payload.get('rows') or [])
now = datetime.now(timezone.utc)

def parse_ts(v):
    s = str(v or '').strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def totals(r):
    tin = r.get('tokens_input')
    tout = r.get('tokens_output')
    if not isinstance(tin, (int,float)) or not isinstance(tout, (int,float)):
        return None
    return int(tin) + int(tout)

# Date ranges
ranges = {
    'all': None,
    '1h': now - timedelta(hours=1),
    '4h': now - timedelta(hours=4),
    '24h': now - timedelta(hours=24),
    '7d': now - timedelta(days=7),
    '30d': now - timedelta(days=30),
}
date_counts = {}
for k, cutoff in ranges.items():
    if cutoff is None:
        date_counts[k] = len(rows)
    else:
        n = 0
        for r in rows:
            ts = parse_ts(r.get('timestamp'))
            if ts is not None and ts >= cutoff:
                n += 1
        date_counts[k] = n

# Token ranges
token_counts = {'all': len(rows), '0_100':0, '101_1000':0, '1001_10000':0, '10001_plus':0}
for r in rows:
    t = totals(r)
    if t is None:
        continue
    if 0 <= t <= 100:
        token_counts['0_100'] += 1
    elif 101 <= t <= 1000:
        token_counts['101_1000'] += 1
    elif 1001 <= t <= 10000:
        token_counts['1001_10000'] += 1
    else:
        token_counts['10001_plus'] += 1

# Sort probes (request_id at top)
def ts_ms(r):
    d = parse_ts(r.get('timestamp'))
    return d.timestamp() if d else 0

sort_probes = {}
if rows:
    time_desc = sorted(rows, key=ts_ms, reverse=True)
    time_asc = sorted(rows, key=ts_ms)
    cost_desc = sorted(rows, key=lambda r: float(r.get('cost_usd') or -1), reverse=True)
    latency_desc = sorted(rows, key=lambda r: int(r.get('latency_ms') or -1), reverse=True)
    sort_probes = {
        'time_desc_top_request_id': str(time_desc[0].get('request_id') or ''),
        'time_asc_top_request_id': str(time_asc[0].get('request_id') or ''),
        'cost_desc_top_request_id': str(cost_desc[0].get('request_id') or ''),
        'latency_desc_top_request_id': str(latency_desc[0].get('request_id') or ''),
    }

out = {
    'row_count': len(rows),
    'date_counts': date_counts,
    'token_counts': token_counts,
    'provider_counts': {
        'vertex': sum(1 for r in rows if str(r.get('provider') or '').strip() == 'vertex'),
        'openai': sum(1 for r in rows if str(r.get('provider') or '').strip() == 'openai'),
        'azure_openai': sum(1 for r in rows if str(r.get('provider') or '').strip() == 'azure_openai'),
    },
    'sort_probes': sort_probes,
}
print(json.dumps(out, ensure_ascii=False))


