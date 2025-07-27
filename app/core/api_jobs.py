
import streamlit as st
import logging, json
from app.models.job_model import JobModel
from streamlit_extras.concurrency_limiter import concurrency_limiter
from ..core import fetch_data






@st.cache_data(ttl=60*60)
def fetch_jobs_offers(company_id, job_id=None) -> list[JobModel] | JobModel:
    try:

        query_params = {"sfilter": json.dumps([["id", "=", job_id], ["ind_Estado", "=","3"]])} if job_id else None
        
        # Fetching job postings from the API
        
        response = fetch_data(endpoint=f"reclutamiento/external/requisicion/compania/{company_id}", params=query_params)
        
        
        result =  response.get("result", None)
       
        jobs = []  

        if result:
            for data in result:
                #if data.get('ind_Estado') == 3:
                job = JobModel(
                            id=data.get("id"),
                            job_title=data.get("nombre_Requisicion"),
                            position_name=data.get("nombre_Puesto"),
                            department_id=data.get("id_Departamento"),
                            department_name=data.get("nombreDepartamento"),
                            company_name=data.get("nombreCompania"),
                            job_description=data.get("descripcion"),
                            contract_type=data.get("tipo_Contrato"),
                            contract_type_name=data.get("nombreTipoContrato"),
                            creation_date=data.get("fecha_Creacion"),
                            requirements=data.get("requisitosPuesto"),
                            responsibilities=data.get("responsabilidadesPuesto"),
                            workMode_code=data.get("modalidad"),
                            workMode=data.get("nombreModalidad"),
                            customData=data.get("customData"),
                        )  
                
                jobs.append(job) 

        if job_id:
            return jobs[0]
           
        return jobs
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    
    
    
@st.cache_data(ttl=60*60)
def fetch_jobs_offer_by_id(job_id, company_id) -> list[JobModel]:
    try:
        query_params = {
            "sort": '[{ "selector": "fecha_Creacion", "desc": True}]'
        }
        query_params = {
            "take": 100
        }
        
        # Fetching job postings from the API
        
        response = fetch_data(endpoint=f"reclutamiento/external/solicitud/requisicion/{job_id}/compania/{company_id}", params=None)
        result =  response.get("result", None)
       
        jobs = []  

        if result:
            for data in result:
                #if data.get('ind_Estado') == 3:
                job = JobModel(
                            id=data.get("id"),
                            job_title=data.get("nombre_Requisicion"),
                            position_name=data.get("nombre_Puesto"),
                            department_id=data.get("id_Departamento"),
                            department_name=data.get("nombreDepartamento"),
                            company_name=data.get("nombreCompania"),
                            job_description=data.get("descripcion"),
                            contract_type=data.get("tipo_Contrato"),
                            contract_type_name=data.get("nombreTipoContrato"),
                            creation_date=data.get("fecha_Creacion"),
                            requirements=data.get("requisitosPuesto"),
                            responsibilities=data.get("responsabilidadesPuesto"),
                            workMode_code=data.get("modalidad"),
                            workMode=data.get("nombreModalidad"),
                            customData=data.get("customData"),
                        )  
                
                jobs.append(job) 

           
        return jobs
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    

  
   
        
@concurrency_limiter(max_concurrency=1)
def apply_job_offert(data: dict, file:dict):

    payload = {
        "solicitud_model": {
                "tipo_Identificacion": data['tipo_Identificacion'],         # Ejemplo, fijo o de otro origen
                "identificacion": data["identificacion"],
                "id_Compania": data["id_Compania"],                 # No está en JobModel, poner fijo o obtener de otro dato
                "primer_Nombre": data["primer_Nombre"],        # No está en JobModel
                "segundo_Nombre": data["segundo_Nombre"],        # No está en JobModel
                "primer_Apellido": data["primer_Apellido"],    # No está en JobModel
                "segundo_Apellido": data["segundo_Apellido"],    # No está en JobModel
                "nombre_Completo": data["nombre_Completo"],   
                "comentario": data["comentario"], 
                "email": data["email"],                       # No está en JobModel
                "telefono":data["telefono"],          # No está en JobModel
                "id_GradoAcademico": data["id_GradoAcademico"].split("-")[0],           
                "etiqueta": data.get("etiqueta", ""),
                "id_Requisicion": data["id_Requisicion"],
                "id_Supervisor": None,  # No está supervisor id, solo nombre
                "id_Departamento": data["id_Departamento"],
                "apreciacion": data["apreciacion"],   
                "origen_Solicitante": 1,  # 1 = Externo, 2 = Interno
                "nombre_Departamento": data["nombre_Departamento"],
                "nombre_Supervisor": data["nombre_Supervisor"],
                "ExtraCustomData": data["ExtraCustomData"],
                "customData": {}
            },
        "archivo_model": {
            "IdSolicitud": 0,
            "archivoNombre": "",
            "Extension": f".{file['fileExtension']}",
            "FileName":"", #Nombre corto del archivo, requerido si se pasa en base64 o buytes
            "ArchivoInBase64": None,
            "ArchivoInBytes":file["attachedDocument"],
            "clasificacionId": 1, #cv,
            "archivoTamano": len(file["attachedDocument"]),
            "unidadMedida": 2, 
            
        }  
    }
    

        
    
    response = fetch_data(endpoint="reclutamiento/External/SolicitudEmpleo", method="POST", body_params=payload)
    #payload["archivo_model"]["ArchivoInBase64"] = payload["archivo_model"]["ArchivoInBase64"][:50]
    # print(payload)
    # print(response)
    if response.get("error", None):
        return response

    return response    