
import streamlit as st
import requests as r
import logging

# Mocking st.secrets and st.session_state for the script
class MockSecrets(dict):
    def __getattr__(self, name):
        return self.get(name)

st.secrets = MockSecrets({
    "enviroment": "apis",
    "apis": [
        {"name": "reclutamiento", "url": "https://api.reclutamiento.triple.com.do"}
    ]
})

st.session_state = {"enviroment": "apis", "domain_name": "demo.triple.com.do"}

def fetch_data(endpoint, method="GET", params=None, body_params=None, headers=None, timeout=60, is_singIn=False, modulo="framework"):
    try:
        headers = {
            "Content-Type": "application/json",
            "x-ui-culture": "es-DO",
            "x-api-key": "002002032323232320002SSS",
            "x-ui-domain": "demo.triple.com.do"
        }
       
        if "domain_name" in st.session_state:
            headers["x-ui-domain"] = st.session_state['domain_name']   
            
        apis = st.secrets[st.session_state["enviroment"]]
        url_base = next((api["url"] for api in apis if api["name"] ==  modulo), None)
        if modulo == "framework":
            url_base = f"{url_base}/fmk"

        url = f"{url_base}/{endpoint}"
        print(f"Requesting: {url}")

        response = r.request(method, url, params=params, json=body_params, headers=headers, timeout=timeout)

        if response.status_code > 300:
            print(f"Status Code: {response.status_code}")
            # This is where the error likely happens
            try:
                error_json = response.json()
                print(f"API Error JSON: {error_json}")
            except Exception as e:
                print(f"Failed to parse error JSON: {e}")
                raise e

        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
            
        return {"error": True, "statuscode": response.status_code, "message": "Non-JSON response"}
    except r.exceptions.RequestException as req_err:
        print(f"Caught RequestException: {req_err}")
        return {"error": f"Request error occurred: {req_err}"}
    except Exception as e:
        print(f"Caught general Exception: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = fetch_data(endpoint="external/requisicion/publicadas", modulo="reclutamiento")
    print(f"Result: {result}")
