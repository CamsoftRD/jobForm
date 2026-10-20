
import streamlit as st
import logging, json
from app.models.job_model import JobModel
from streamlit_extras.concurrency_limiter import concurrency_limiter
from ..core import fetch_data






def parse_work_mode(modalidad, nombre_modalidad=None) -> str:
    """
    Normaliza y resuelve la modalidad de trabajo (Presencial, Remoto, Híbrido).
    """
    mapping = {
        1: "Presencial",
        2: "Remoto",
        3: "Híbrido",
        "1": "Presencial",
        "2": "Remoto",
        "3": "Híbrido",
        "presencial": "Presencial",
        "remoto": "Remoto",
        "remota": "Remoto",
        "hibrido": "Híbrido",
        "híbrido": "Híbrido",
    }
    
    # 1. Si modalidad viene como código numérico o texto reconocido
    if modalidad is not None:
        if modalidad in mapping:
            return mapping[modalidad]
        mod_str = str(modalidad).strip().lower()
        if mod_str in mapping:
            return mapping[mod_str]
            
    # 2. Si nombre_modalidad viene informado y es válido
    if nombre_modalidad and str(nombre_modalidad).strip():
        nm_clean = str(nombre_modalidad).strip()
        if nm_clean.lower() in mapping:
            return mapping[nm_clean.lower()]
        return nm_clean.capitalize()
        
    return "Presencial"


@st.cache_data(ttl=30, show_spinner=False)
def fetch_jobs_offers(company_id, job_id=None) -> list[JobModel] | JobModel:
    try:

        query_params = {"sfilter": json.dumps([["id", "=", job_id], ["ind_Estado", "=","3"]])} if job_id else {"sfilter": json.dumps([["ind_Estado", "=","3"]])}
        
        # Fetching job postings from the API
        
        response = fetch_data(endpoint=f"external/requisicion/compania/{company_id}", params=query_params, modulo="reclutamiento")
        

        result =  response.get("result", None)
       
        jobs = []  

        if result:
            for data in result:
                if data.get('ind_Estado') == 3:
                    job = JobModel(
                                id=data.get("id"),
                                job_title=data.get("nombre_Requisicion"),
                                position_name=data.get("nombre_Puesto"),
                                department_id=data.get("id_Departamento"),
                                department_name=data.get("nombreDepartamento"),
                                company_id=data.get("id_Compania"),
                                company_name=data.get("nombreCompania"),
                                job_description=data.get("descripcion"),
                                contract_type=data.get("tipo_Contrato"),
                                contract_type_name=data.get("nombreTipoContrato"),
                                creation_date=data.get("fecha_Creacion"),
                                requirements=data.get("requisitos"),
                                responsibilities=data.get("responsabilidades"),
                                workMode_code=data.get("modalidad"),
                                workMode=parse_work_mode(data.get("modalidad"), data.get("nombreModalidad")),
                                customData=data.get("extraCustomData"),
                                imageUrl=data.get("urlImagenVacante"),
                                location=data.get("ubicacion", "")
                            )  
                    
                    jobs.append(job) 

        if job_id:
            if jobs:
                return jobs[0]
            else:
                return {"error": "No se encontró el empleo solicitado o no está disponible."}
           
        return jobs
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    
    
  
  
  
  

def fetch_jobs_offers_by_group(id_grupo_economico, job_id=None) -> list[JobModel] | JobModel:
    try:

        #query_params = {"sfilter": json.dumps([["id", "=", job_id], ["ind_Estado", "=","3"]])} if job_id else None
        query_params = {"sfilter": json.dumps([["id", "=", job_id], ["ind_Estado", "=","3"]])} if job_id else {"sfilter": json.dumps([["ind_Estado", "=","3"]])}
        
        
        # Fetching job postings from the API
        
        #response = fetch_data(endpoint=f"external/requisicion/grupo/{id_grupo_economico}", params=query_params, modulo="reclutamiento")
        response = fetch_data(endpoint=f"external/requisicion/publicadas", params=query_params, modulo="reclutamiento")
        
        
        result =  response.get("result", None)

       
        jobs = []  

        if result:
            for data in result:
               
                    job = JobModel(
                                id=data.get("id"),
                                job_title=data.get("nombre_Requisicion"),
                                position_name=data.get("nombre_Puesto"),
                                department_id=data.get("id_Departamento"),
                                department_name=data.get("nombreDepartamento"),
                                company_id=data.get("id_Compania"),
                                company_name=data.get("nombreCompania"),
                                job_description=data.get("descripcion"),
                                contract_type=data.get("tipo_Contrato"),
                                contract_type_name=data.get("nombreTipoContrato"),
                                creation_date=data.get("fecha_Creacion"),
                                requirements=data.get("requisitos"),
                                responsibilities=data.get("responsabilidades"),
                                workMode_code=data.get("modalidad"),
                                workMode=parse_work_mode(data.get("modalidad"), data.get("nombreModalidad")),
                                customData=data.get("customData"),
                                imageUrl=data.get("urlImagenVacante"),
                                location=data.get("ubicacion", "")
                            )  
                    
                    jobs.append(job) 

        if job_id:
            if jobs:
                return jobs[0]
            else:
                return {"error": "No se encontró el empleo solicitado o no está disponible."}
           
        return jobs
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    
   
   
       

def fetch_jobs_offer_by_id(job_id, company_id) -> list[JobModel]:
    try:
        query_params = {
            "sort": '[{ "selector": "fecha_Creacion", "desc": True}]'
        }
        query_params = {
            "take": 100
        }
        
        # Fetching job postings from the API
        
        response = fetch_data(endpoint=f"external/solicitud/requisicion/{job_id}/compania/{company_id}", params=None, modulo="reclutamiento")
        result =  response.get("result", None)
       
        jobs = []  

        if result:
            for data in result:
                if data.get('ind_Estado') == 3:
                    job = JobModel(
                                id=data.get("id"),
                                job_title=data.get("nombre_Requisicion"),
                                position_name=data.get("nombre_Puesto"),
                                department_id=data.get("id_Departamento"),
                                department_name=data.get("nombreDepartamento"),
                                company_id=data.get("id_Compania"),
                                company_name=data.get("nombreCompania"),
                                job_description=data.get("descripcion"),
                                contract_type=data.get("tipo_Contrato"),
                                contract_type_name=data.get("nombreTipoContrato"),
                                creation_date=data.get("fecha_Creacion"),
                                requirements=data.get("requisitos"),
                                responsibilities=data.get("responsabilidades"),
                                workMode_code=data.get("modalidad"),
                                workMode=parse_work_mode(data.get("modalidad"), data.get("nombreModalidad")),
                                customData=data.get("customData"),
                                imageUrl=data.get("urlImagenVacante"),
                                location=data.get("ubicacion", "")
                            )  
                    
                    jobs.append(job) 

           
        return jobs
    except Exception as e:
        logging.error(f"an error has occurred: {e}")
        return {"error": str(e)}
    

  
   
        
@concurrency_limiter(max_concurrency=1)
def apply_job_offert(data: dict, file: dict = None):

    archivo_model = {
        "IdSolicitud": 0,
        "archivoNombre": "",
        "Extension": f".{file['fileExtension']}" if file and file.get("fileExtension") else "",
        "FileName": "",
        "ArchivoInBase64": None,
        "ArchivoInBytes": file.get("attachedDocument") if file else None,
        "clasificacionId": 1,  # cv
        "archivoTamano": len(file.get("attachedDocument")) if file and file.get("attachedDocument") else 0,
        "unidadMedida": 2,
    }

    payload = {
        "solicitud_model": {
            "tipo_Identificacion": data['tipo_Identificacion'],
            "identificacion": data["identificacion"],
            "id_Compania": data["id_Compania"],
            "primer_Nombre": data["primer_Nombre"],
            "segundo_Nombre": data.get("segundo_Nombre"),
            "primer_Apellido": data["primer_Apellido"],
            "segundo_Apellido": data.get("segundo_Apellido"),
            "nombre_Completo": data["nombre_Completo"],
            "comentario": data.get("comentario", ""),
            "email": data["email"],
            "telefono": data["telefono"],
            "id_GradoAcademico": data.get("id_GradoAcademico"),
            "etiqueta": data.get("etiqueta", ""),
            "id_Requisicion": data["id_Requisicion"],
            "id_Supervisor": None,
            "id_Departamento": data["id_Departamento"],
            "apreciacion": data.get("apreciacion", 0),
            "origen_Solicitante": 1,  # 1 = Externo, 2 = Interno
            "nombre_Departamento": data.get("nombre_Departamento", ""),
            "nombre_Supervisor": data.get("nombre_Supervisor", ""),
            "ExtraCustomData": data.get("ExtraCustomData", "[]"),
            "customData": data.get("customData", {})
        },
        "archivo_model": archivo_model
    }
    
    #escribir payload en un archivo .json
    with open("payloads.json", "w") as f:
        json.dump(payload, f, indent=4)        

        
    
    response = fetch_data(endpoint="External/SolicitudEmpleo", method="POST", body_params=payload, modulo="reclutamiento")
    #payload["archivo_model"]["ArchivoInBase64"] = payload["archivo_model"]["ArchivoInBase64"][:50]
    # print(payload)
    # print(response)
    if response.get("error", None):
        return response

    return response    