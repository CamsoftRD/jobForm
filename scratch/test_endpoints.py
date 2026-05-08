
import requests as r

headers = {
    "Content-Type": "application/json",
    "x-ui-culture": "es-DO",
    "x-api-key": "002002032323232320002SSS",
    "x-ui-domain": "demo.triple.com.do"
}

endpoints = [
    "https://api.reclutamiento.triple.com.do/external/requisicion/publicadas",
    "https://api.reclutamiento.triple.com.do/external/requisicion/grupo/5",
    "https://api.reclutamiento.triple.com.do/external/requisicion/grupo/1"
]

for url in endpoints:
    print(f"Testing URL: {url}")
    try:
        response = r.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Found {len(data.get('result', []))} jobs")
            except:
                print("Response is not JSON")
        else:
            print(f"Response: {response.text[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
