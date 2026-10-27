"""Fetch Toggl Track time entries via API v9 and write data.json for the dashboard.

Env:
  TOGGL_API_TOKEN  (required)  Toggl Profile settings -> API Token
  START_DATE       (optional)  first day ever to include, YYYY-MM-DD (default 2026-09-01)
  REFETCH_DAYS     (optional)  re-fetch this many recent days each run (default 60)
  OUT              (optional)  output path (default data.json)

Each run keeps the records already in data.json that are older than the re-fetch window
and re-fetches the window in 7-day chunks (the v9 endpoint caps one response at ~1000
entries, so large chunks silently drop the oldest ones). Edits made in Toggl within the
window are picked up; history older than the window is preserved as-is.
Times are converted to Asia/Tokyo and written without offset, which is what index.html expects.
"""
import base64, datetime as dt, json, os, sys, time, urllib.request, urllib.parse
from zoneinfo import ZoneInfo

TOKEN = os.environ.get('TOGGL_API_TOKEN')
if not TOKEN:
    sys.exit('TOGGL_API_TOKEN is not set')
START = dt.date.fromisoformat(os.environ.get('START_DATE', '2026-09-01'))
OUT = os.environ.get('OUT', 'data.json')
REFETCH_DAYS = int(os.environ.get('REFETCH_DAYS', '60'))
JST = ZoneInfo('Asia/Tokyo')
API = 'https://api.track.toggl.com/api/v9'
AUTH = 'Basic ' + base64.b64encode(f'{TOKEN}:api_token'.encode()).decode()


def get(path, params=None):
    url = API + path + (('?' + urllib.parse.urlencode(params)) if params else '')
    req = urllib.request.Request(url, headers={'Authorization': AUTH, 'Content-Type': 'application/json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 * (attempt + 1)); continue
            raise


me = get('/me')
wid = me['default_workspace_id']
projects = {p['id']: p['name'] for p in (get('/me/projects', {'include_archived': 'true'}) or [])}

today = dt.datetime.now(JST).date()
fetch_from = max(START, today - dt.timedelta(days=REFETCH_DAYS))

kept = []
if os.path.exists(OUT):
    try:
        kept = [r for r in json.load(open(OUT, encoding='utf8'))['records']
                if START.isoformat() <= r['s'][:10] < fetch_from.isoformat()]
    except Exception as ex:
        print('could not read existing data:', ex)

entries, cur = [], fetch_from
while cur <= today:
    end = min(cur + dt.timedelta(days=6), today)
    # end_date is exclusive; pad a day on both sides so UTC/JST boundaries never drop entries
    chunk = get('/me/time_entries', {'start_date': (cur - dt.timedelta(days=1)).isoformat(),
                                     'end_date': (end + dt.timedelta(days=2)).isoformat()}) or []
    if len(chunk) >= 900:
        sys.exit(f'chunk {cur}..{end} returned {len(chunk)} entries; response may be truncated')
    entries.extend(chunk)
    cur = end + dt.timedelta(days=1)

seen, recs = set(), []
for e in entries:
    if e.get('workspace_id') not in (None, wid):
        continue
    if e['id'] in seen or e.get('duration', -1) < 0 or not e.get('stop'):
        continue  # running timer or duplicate across chunk borders
    seen.add(e['id'])
    s = dt.datetime.fromisoformat(e['start'].replace('Z', '+00:00')).astimezone(JST)
    t = dt.datetime.fromisoformat(e['stop'].replace('Z', '+00:00')).astimezone(JST)
    if s.date() < fetch_from:
        continue
    tags = e.get('tags') or []
    recs.append({
        'd': e.get('description') or '(no description)',
        'p': projects.get(e.get('project_id'), '-') if e.get('project_id') else '-',
        't': ', '.join(tags) if tags else '-',
        's': s.strftime('%Y-%m-%dT%H:%M:%S'),
        'e': t.strftime('%Y-%m-%dT%H:%M:%S'),
    })
recs = kept + recs
recs.sort(key=lambda x: x['s'])

json.dump({'generated': dt.datetime.now(JST).strftime('%Y-%m-%dT%H:%M:%S'), 'tz': 'Asia/Tokyo', 'records': recs},
          open(OUT, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(f'kept {len(kept)} + fetched {len(recs) - len(kept)} = {len(recs)} entries, {recs[0]["s"] if recs else "-"} .. {recs[-1]["e"] if recs else "-"} -> {OUT}')
