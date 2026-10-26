import streamlit as st
import json

# Mock secrets for testing
st.secrets = {
    "domain": {
        "jobsdev.triple.com.do": "test.triple.com.do",
        "jobs.triple.com.do": "mallen.triple.com.do"
    },
    "economic_groups": {
        "test.triple.com.do": 1,
        "mallen.triple.com.do": 2
    }
}

# Mock session state
st.session_state = {"domain_name": "test.triple.com.do"}
st.query_params = {}

# Test Logic
economic_groups = st.secrets.get("economic_groups", {})
mapped_domain = st.session_state.get("domain_name")
id_grupo_economico = economic_groups.get(mapped_domain, st.query_params.get("geco", 1))

print(f"Mapped Domain: {mapped_domain}")
print(f"Economic Group ID: {id_grupo_economico}")

# Test with another domain
st.session_state["domain_name"] = "mallen.triple.com.do"
mapped_domain = st.session_state.get("domain_name")
id_grupo_economico = economic_groups.get(mapped_domain, st.query_params.get("geco", 1))

print(f"Mapped Domain: {mapped_domain}")
print(f"Economic Group ID: {id_grupo_economico}")

# Test fallback
st.session_state["domain_name"] = "unknown.com"
mapped_domain = st.session_state.get("domain_name")
id_grupo_economico = economic_groups.get(mapped_domain, st.query_params.get("geco", 1))

print(f"Mapped Domain: {mapped_domain}")
print(f"Economic Group ID: {id_grupo_economico} (Expected: 1 from default query param)")
