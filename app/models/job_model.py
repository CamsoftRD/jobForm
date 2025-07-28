from dataclasses import dataclass
from typing import Optional

@dataclass
class JobModel:
    id: Optional[int] = None
    job_title: Optional[str] = None  # Nombre del puesto
    position_name: Optional[str] = None  # Nombre del puesto
    department_id: Optional[int] = None  # id del departamento
    department_name: Optional[str] = None  # Nombre del departamento
    company_id: Optional[int] = None  # id del compania
    company_name: Optional[str] = None  # Nombre de la compañía
    job_description: Optional[str] = None  # Descripción del puesto
    contract_type: Optional[int] = None  # Tipo de contrato
    contract_type_name: Optional[str] = None  # Tipo de contrato
    creation_date: Optional[str] = None  # Fecha de creación
    closing_date: Optional[str] = None  # Fecha de cierre
    supervisor_name: Optional[str] = None  # Nombre del supervisor
    requirements: Optional[str] = None  # Requisitos del puesto
    responsibilities: Optional[str] = None  # Responsabilidades del puesto
    available_positions: Optional[int] = None  # Cantidad de posiciones disponibles
    workMode_code: Optional[int] = None # modalidad codigo 
    workMode: Optional[str] = None # modalidad descripcion,  remota, presencial, hibrido 
    salary: Optional[float] = None # modalidad descripcion,  remota, presencial, hibrido 
    customData: Optional[str] = None  # Datos personalizados del empleo, si existen
    
    