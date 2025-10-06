
import requests as r
import logging
import streamlit as st

base_url = st.secrets["base_url"]


def fetch_data(endpoint, method="GET", params=None, body_params=None, headers=None, timeout=60, is_singIn=False, modulo="framework"):
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
            "x-ui-domain": "mallen.triple.com.do"
        }
        api = base_url
        
        if modulo ==  "reclutamiento":
             api = "https://api.reclutamiento.triple.com.do"
        
        elif modulo == "empleados":
            api = "https://api.empleados.triple.com.do"
        elif modulo == "administracion":
            api = "https://api.administracion.triple.com.do"
        elif modulo == "framework":
            api = "https://api.framework.triple.com.do"
        
          
        url = f"{api}/{endpoint}"
        
  
            
   
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




def send_email(email, subject, body):
    """Send Email"""
    # Obtener el id del usuario de la sesión        
   
    payload = {
        "Destinatarios": email,
        "Titulo": subject,
        "Cuerpo": body
        
    }
 
    response = fetch_data(endpoint="EnviarEmail", method="POST", body_params=payload, modulo="framework")
    data  = response.get("result", None)
    print(f"Response from send_email: {response}")
    return data


def validate_employee(employee_id, employee_company):
    response = fetch_data(endpoint=f"external/empleado/{employee_id}/compania/{employee_company}", modulo="empleados")    
    return response
    
 

    