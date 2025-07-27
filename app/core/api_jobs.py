
import streamlit as st
import logging, json
from app.models.job_model import JobModel
from streamlit_extras.concurrency_limiter import concurrency_limiter
import requests as r




def fetch_data(endpoint, method="GET", params=None, body_params=None, headers=None, timeout=60, is_singIn=False):
    """
    Función genérica para realizar solicitudes HTTP.

    :param endpoint: Endpoint de la API.
    :param method: Método HTTP (GET, POST, etc.).
    :param params: Parámetros de consulta.
    :param body_params: Datos del cuerpo de la solicitud.
    :param headers: Encabezados adicionales.
    :param timeout: Tiempo de espera en segundos.
    :return: Respuesta en formato JSON o texto.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "x-ui-culture": "es-DO",
            "x-api-key": "002002032323232320002SSS",
            "x-ui-domain": "rrhh.administracion.camsoft.com.do_8086"
        }
          
        url = f"http://rrhh.administracionapi.camsoft.com.do:8086/{endpoint}"
        
  
            
   
        # aviat.triple.com.do/jobs -> jobs.triple.com.do
        
        # obtergo : aviat.triple.com.do/jobs
        # nomina.trim
        
        #print(f"Request domain: {headers['x-ui-domain']}")
        
     
   
        
        response = r.request(method, url, params=params, json=body_params, headers=headers, timeout=timeout)

        
        #logging.error(response.text)
        if response.status_code > 300:
            logging.error(f"API Error: {response.json()}")  # Registrar el error en el logger

        #response.raise_for_status()
        #print(response.status_code, response.url, response.text)
        
        # Verificar si la respuesta es JSON
        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()

            # Manejar errores específicos del esquema
            if "errorCode" in data:
                logging.error(f"API Error: {data}")  # Registrar el error en el logger
                
                
                return {
                    "error": True,
                    "errorCode": data.get("errorCode"),
                    "errorId": data.get("errorId"),
                    "message": data.get("message"),
                    "detail": data.get("detail"),
                    "statuscode": data.get("statuscode"),
                    "redirectUrl": data.get("redirectUrl"),
                }

            return data  # Retornar la respuesta JSON si no hay errores
            
        #return response.text  # Retornar texto si no es JSON
        logging.error(f"Non-JSON response: {response.text}")  # Registrar el error en el logger
        return {"error": True, "statuscode": response.status_code, "message": f"Ha ocurrido un error al procesar la solicitud."}
    except r.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")  # Registrar el error HTTP
        return {"error": f"HTTP error occurred: {http_err}"}
    except r.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")  # Registrar el error de solicitud
        return {"error": f"Request error occurred: {req_err}"}






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
                "id_GradoAcademico": data["id_GradoAcademico"].split("-")[0],            # No está en JobModel
                "etiqueta": data["etiqueta"],
                "id_Requisicion": data["id_Requisicion"],
                "id_Supervisor": None,  # No está supervisor id, solo nombre
                "id_Departamento": data["id_Departamento"],
                "apreciacion": data["apreciacion"],   
                "origen_Solicitante": 2,  # Valor fijo ejemplo
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