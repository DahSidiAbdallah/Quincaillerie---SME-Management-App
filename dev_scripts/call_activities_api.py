#!/usr/bin/env python3
import urllib.request, json
url='http://127.0.0.1:5000/api/dashboard/activities?limit=50'
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        text = r.read().decode('utf-8')
        try:
            data = json.loads(text)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print('Non-JSON response:', text)
except Exception as e:
    print('HTTP error:', e)
