from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta

from src.config.manager import ConfigManager
from src.data.usage_db import UsageDatabase

cfg = ConfigManager()
connections = cfg.list_connections()
if not connections:
    raise SystemExit('NO_CONNECTIONS')

picked = []
for c in connections:
    cid = str((c or {}).get('id') or '').strip()
    name = str((c or {}).get('connection_name') or '').strip() or cid
    if cid:
        picked.append((cid, name))
    if len(picked) >= 3:
        break
if not picked:
    raise SystemExit('NO_VALID_CONNECTIONS')
while len(picked) < 3:
    picked.append(picked[0])

model_ids = ['gpt-4o-mini', 'claude-3-5-haiku', 'llama-3.1-8b']
providers = ['openai', 'anthropic', 'ollama']

db = UsageDatabase()
now = datetime.now(timezone.utc)
seed_tag = now.strftime('%Y%m%d%H%M%S')
inserted = []

for i in range(3):
    conn_id, conn_name = picked[i]
    model_id = model_ids[i]
    provider = providers[i]
    ts = now - timedelta(minutes=(i + 1))
    req_id = f'fake-modelid-{seed_tag}-{i+1:02d}'
    db.log_usage(
        agent_id=conn_id,
        agent_name=conn_name,
        tokens_input=42 + i,
        tokens_output=21 + i,
        cost_usd=0.001 + (i * 0.0005),
        timestamp=ts.isoformat(),
        latency_ms=700 + (i * 100),
        status='success',
        error_type=None,
        request_id=req_id,
        provider=provider,
        model_id=model_id,
    )
    inserted.append({
        'request_id': req_id,
        'connection_id': conn_id,
        'connection_name': conn_name,
        'provider': provider,
        'model_id': model_id,
        'timestamp': ts.isoformat(),
    })

print(json.dumps({'inserted_count': len(inserted), 'rows': inserted}, ensure_ascii=False))
