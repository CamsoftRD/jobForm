
import streamlit as st
import requests as r
import logging

# Mocking st.secrets and st.session_state for the script
class MockSecrets(dict):
    def __getattr__(self, name):
        return self.get(name)

st.secrets = MockSecrets({
    "enviroment": "apis_qa",
    "apis_qa": [
        {"name": "reclutamiento", "url": "https://api.reclutamientoqa.triple.com.do"}
    ]
})

st.session_state = {"enviroment": "apis_qa", "domain_name": "test.triple.com.do"}

def fetch_data(endpoint, method="GET", params=None, body_params=None, headers=None, timeout=60, is_singIn=False, modulo="framework"):
    try:
        headers = {
            "Content-Type": "application/json",
            "x-ui-culture": "es-DO",
            "x-api-key": "002002032323232320002SSS",
            "x-ui-domain": "test.triple.com.do"
        }
       
        apis = st.secrets[st.session_state["enviroment"]]
        url_base = next((api["url"] for api in apis if api["name"] ==  modulo), None)
        if modulo == "framework":
            url_base = f"{url_base}/fmk"

        url = f"{url_base}/{endpoint}"
        print(f"Requesting: {url}")

        response = r.request(method, url, params=params, json=body_params, headers=headers, timeout=timeout)

        if response.status_code > 300:
            try:
                error_data = response.json()
                print(f"API Error ({response.status_code}): {error_data}")
            except Exception:
                print(f"API Error ({response.status_code}): {response.text[:100]}...")

        if response.headers.get("Content-Type", "").startswith("application/json"):
            try:
                return response.json()
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
            
        return {"error": True, "statuscode": response.status_code, "message": "Non-JSON response"}
    except Exception as e:
        print(f"Caught exception: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test the NEW endpoint with QA environment
    result = fetch_data(endpoint="external/requisicion/grupo/5", modulo="reclutamiento")
    print(f"Result (len): {len(result.get('result', [])) if isinstance(result, dict) else 'N/A'}")
    
    # Test a 404 endpoint to ensure no crash
    print("\nTesting 404 endpoint:")
    result_404 = fetch_data(endpoint="external/requisicion/publicadas", modulo="reclutamiento")
    print(f"Result 404: {result_404}")
