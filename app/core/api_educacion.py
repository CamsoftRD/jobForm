
import streamlit as st
from app.models.educacion_model import GradoModel
from ..core import fetch_data
import logging



@st.cache_data(ttl=60*60)
def fetch_grades() -> list[GradoModel]:
    try:

        #query_params = {"sfilter": json.dumps([["id", "=", job_id], ["ind_Estado", "=","3"]])} if job_id else None
        
        # Fetching job postings from the API
        
        response = fetch_data(endpoint=f"external/gradoacademico", modulo="administracion")
        
        
        result =  response.get("result", None)
       
        grados = []  

        if result:
            for data in result:
                #if data.get('ind_Estado') == 3:
                grado = GradoModel(
                    codigo=data.get("codigo"),
                    nombre=data.get("nombre"),
                    ind_Estado=data.get("ind_Estado"),
                    nombre_Estado=data.get("nombre_Estado"),
                    customData=data.get("customData"),
                    customData2=data.get("customData2"),
                ) 
                
                grados.append(grado) 


        return grados
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    