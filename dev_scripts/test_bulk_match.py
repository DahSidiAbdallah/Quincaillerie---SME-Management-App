#!/usr/bin/env python3
import urllib.request, json
url = 'http://127.0.0.1:5000/api/dashboard/activities/bulk-match'
req = urllib.request.Request(url, method='POST')
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode('utf-8'))
        print('success:', data.get('success'))
        results = data.get('results', [])
        print('results_count:', len(results))
        for item in results[:5]:
            print('activity', item['activity_id'], 'candidates', len(item.get('candidates', [])))
except Exception as e:
    print('error', e)
