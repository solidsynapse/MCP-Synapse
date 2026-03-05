from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.config.manager import ConfigManager
from src.data.usage_db import UsageDatabase

cfg = ConfigManager()
conns = [c for c in cfg.list_connections() if isinstance(c, dict) and str(c.get('id') or '').strip()]
if not conns:
    raise SystemExit('NO_CONNECTIONS')

# Pick up to 3 connections; fallback to first for all rows.
picked = conns[:3]
while len(picked) < 3:
    picked.append(picked[0])

connA, connB, connC = picked[0], picked[1], picked[2]

conn_specs = [
    (str(connA.get('id') or '').strip(), str(connA.get('connection_name') or '').strip() or 'connA'),
    (str(connB.get('id') or '').strip(), str(connB.get('connection_name') or '').strip() or 'connB'),
    (str(connC.get('id') or '').strip(), str(connC.get('connection_name') or '').strip() or 'connC'),
]

now = datetime.now(timezone.utc)
seed_tag = now.strftime('%Y%m%d%H%M%S')

db = UsageDatabase()
before_rows = db.get_recent_usage(limit=500)
before_count = len(before_rows)

# offset_hours, provider, tokens_in, tokens_out, cost, latency, conn_index, status
blueprint = [
    (0.2, 'vertex', 20, 12, 0.0003, 820, 0, 'success'),
    (0.4, 'openai', 55, 35, 0.0012, 910, 1, 'success'),
    (0.6, 'azure_openai', 120, 60, 0.0048, 980, 2, 'success'),
    (0.8, 'vertex', 600, 500, 0.0123, 1320, 0, 'success'),
    (1.2, 'openai', 7000, 5200, 0.2100, 2100, 1, 'error'),
    (2.0, 'azure_openai', 90, 20, 0.0010, 650, 2, 'success'),
    (3.0, 'vertex', 300, 200, 0.0070, 760, 0, 'success'),
    (4.0, 'openai', 40, 25, 0.0009, 610, 1, 'success'),
    (6.0, 'azure_openai', 80, 35, 0.0011, 700, 2, 'success'),
    (9.0, 'vertex', 250, 120, 0.0050, 880, 0, 'success'),
    (12.0, 'openai', 520, 280, 0.0110, 990, 1, 'success'),
    (20.0, 'azure_openai', 1200, 900, 0.0340, 1700, 2, 'error'),
    (30.0, 'vertex', 35, 20, 0.0007, 530, 0, 'success'),
    (48.0, 'openai', 400, 250, 0.0095, 1200, 1, 'success'),
    (72.0, 'azure_openai', 150, 110, 0.0042, 980, 2, 'success'),
    (96.0, 'vertex', 5000, 4200, 0.1600, 2400, 0, 'error'),
    (120.0, 'openai', 30, 18, 0.0006, 540, 1, 'success'),
    (144.0, 'azure_openai', 90, 40, 0.0015, 730, 2, 'success'),
    (168.0, 'vertex', 2500, 1600, 0.0820, 1850, 0, 'success'),
    (192.0, 'openai', 60, 25, 0.0011, 680, 1, 'success'),
    (240.0, 'azure_openai', 100, 60, 0.0017, 760, 2, 'success'),
    (336.0, 'vertex', 450, 200, 0.0102, 940, 0, 'success'),
    (480.0, 'openai', 80, 30, 0.0015, 720, 1, 'success'),
    (720.0, 'azure_openai', 60, 20, 0.0011, 700, 2, 'success'),
    (960.0, 'vertex', 35, 12, 0.0004, 610, 0, 'success'),  # 40d old
    (1200.0, 'openai', 45, 20, 0.0008, 640, 1, 'success'), # 50d old
]

inserted = []
for idx, spec in enumerate(blueprint, start=1):
    offset_h, provider, tin, tout, cost, latency, conn_idx, status = spec
    conn_id, conn_name = conn_specs[conn_idx]
    ts = now - timedelta(hours=float(offset_h))
    req_id = f"fake-{seed_tag}-{idx:03d}"
    db.log_usage(
        agent_id=conn_id,
        agent_name=conn_name,
        tokens_input=int(tin),
        tokens_output=int(tout),
        cost_usd=float(cost),
        timestamp=ts.isoformat(),
        latency_ms=int(latency),
        status=status,
        error_type='runtime' if status == 'error' else None,
        request_id=req_id,
        provider=provider,
        model_id='seed-model-ignored-by-op',
    )
    inserted.append({
        'request_id': req_id,
        'provider': provider,
        'total_tokens': int(tin) + int(tout),
        'timestamp': ts.isoformat(),
        'connection_id': conn_id,
        'connection_name': conn_name,
        'status': status,
    })

after_rows = db.get_recent_usage(limit=500)
after_count = len(after_rows)

# Basic stats for verification.
provider_counts = {}
for row in inserted:
    provider_counts[row['provider']] = provider_counts.get(row['provider'], 0) + 1

bucket_counts = {'0_100':0,'101_1000':0,'1001_10000':0,'10001_plus':0}
for row in inserted:
    t = row['total_tokens']
    if 0 <= t <= 100:
        bucket_counts['0_100'] += 1
    elif 101 <= t <= 1000:
        bucket_counts['101_1000'] += 1
    elif 1001 <= t <= 10000:
        bucket_counts['1001_10000'] += 1
    else:
        bucket_counts['10001_plus'] += 1

out = {
    'seed_tag': seed_tag,
    'before_count_500': before_count,
    'after_count_500': after_count,
    'inserted_count': len(inserted),
    'provider_counts': provider_counts,
    'token_bucket_counts': bucket_counts,
    'connections_used': conn_specs,
    'first_5_request_ids': [r['request_id'] for r in inserted[:5]],
    'last_5_request_ids': [r['request_id'] for r in inserted[-5:]],
}
print(json.dumps(out, ensure_ascii=False))
