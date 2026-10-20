from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import json

@dataclass
class ApplicantModel:
    # 1. Datos Personales e Identificación
    tipo_Identificacion: int = 1  # 1: Cédula, 5: Pasaporte
    identificacion: str = ""
    primer_Nombre: str = ""
    segundo_Nombre: str = ""
    primer_Apellido: str = ""
    segundo_Apellido: str = ""
    genero: str = ""  # Masculino, Femenino (Requerido)
    fecha_Nacimiento: str = ""  # DD/MM/AAAA (Requerido)
    nacionalidad: str = "Dominicana"
    
    # 2. Contacto y Ubicación
    email: str = ""
    telefono: str = ""
    telefono_Alternativo: str = ""
    ciudad: str = ""
    direccion: str = ""  # Sector o Dirección residencial (Requerido)
    
    # 3. Formación Académica
    id_GradoAcademico: Optional[int] = None
    grado_Nombre: str = ""
    carrera: str = ""
    institucion: str = ""
    estado_Estudios: str = "Graduado"  # Graduado, En curso, Incompleto
    periodo_Estudio: str = ""  # Años cursados (ej: 2018 - 2022)
    
    # 4. Experiencia y Perfil Laboral
    experiencia_Total: str = ""  # Rango general (ej: 1-2 años, 3-5 años...)
    experiencias_Laborales: List[Dict[str, str]] = field(default_factory=list)  # Lista de dicts: empresa, puesto, duracion, funciones
    expectativa_Salarial: str = ""  # Requerido
    disponibilidad: str = "Inmediata"  # Inmediata, 15 días, 1 mes, A convenir
    linkedin_Url: str = ""
    
    # Metadatos del análisis / IA
    etiqueta: str = ""
    comentario: str = ""
    apreciacion: int = 0
    
    @property
    def nombre_Completo(self) -> str:
        parts = [
            self.primer_Nombre.strip(),
            self.segundo_Nombre.strip() if self.segundo_Nombre else "",
            self.primer_Apellido.strip(),
            self.segundo_Apellido.strip() if self.segundo_Apellido else ""
        ]
        return " ".join([p for p in parts if p]).strip()

    def generar_comentario_evaluador(self) -> str:
        """
        Consolida la valoración inicial de la IA junto con el desglose de
        experiencias laborales, formación y datos de contratación para que el
        evaluador pueda leerlo directamente de forma ejecutiva.
        """
        lineas = []

        # 1. Valoración cualitativa de la IA (si existe)
        if self.comentario and self.comentario.strip():
            lineas.append("VALORACIÓN INICIAL IA:")
            lineas.append(self.comentario.strip())
            lineas.append("")

        # 2. Desglose de Experiencias Laborales
        lineas.append("💼 EXPERIENCIAS LABORALES:")
        exps_validas = [
            e for e in self.experiencias_Laborales
            if isinstance(e, dict) and (e.get("empresa") or e.get("puesto") or e.get("funciones"))
        ]
        if exps_validas:
            for idx, exp in enumerate(exps_validas, start=1):
                puesto = exp.get("puesto") or "Puesto no especificado"
                empresa = exp.get("empresa") or "Empresa no especificada"
                duracion = exp.get("duracion") or "Duración no especificada"
                funciones = exp.get("funciones") or "No especificadas"
                lineas.append(f"{idx}. {puesto} en {empresa} | Período: {duracion}")
                if funciones and funciones != "No especificadas":
                    lineas.append(f"   • Funciones: {funciones}")
        else:
            lineas.append(f"• Rango general: {self.experiencia_Total or 'Sin experiencia laboral registrada'}")

        lineas.append("")

        # 3. Formación Académica
        lineas.append("🎓 FORMACIÓN ACADÉMICA:")
        educacion_parts = [self.grado_Nombre or "Nivel no especificado"]
        if self.carrera:
            educacion_parts.append(f"en {self.carrera}")
        if self.institucion:
            educacion_parts.append(f"- {self.institucion}")
        if self.periodo_Estudio:
            educacion_parts.append(f"({self.periodo_Estudio})")
        if self.estado_Estudios:
            educacion_parts.append(f"[{self.estado_Estudios}]")
        lineas.append(f"• {' '.join(educacion_parts)}")

        lineas.append("")

        # 4. Datos clave de contratación
        lineas.append("📋 DATOS DE CONTRATACIÓN:")
        lineas.append(f"• Expectativa Salarial: RD$ {self.expectativa_Salarial or 'A convenir'}")
        lineas.append(f"• Disponibilidad: {self.disponibilidad or 'Inmediata'}")
        if self.ciudad or self.direccion:
            ubicacion = f"{self.direccion or ''}, {self.ciudad or ''}".strip(", ")
            lineas.append(f"• Ubicación: {ubicacion}")
        if self.linkedin_Url:
            lineas.append(f"• LinkedIn / Portafolio: {self.linkedin_Url}")

        return "\n".join(lineas)

    def to_solicitud_dict(self, job: dict, custom_fields_json: str = "[]") -> dict:
        """
        Genera el diccionario compatible con la estructura que espera la API
        'External/SolicitudEmpleo'.
        """
        exps_validas = [
            e for e in self.experiencias_Laborales
            if isinstance(e, dict) and (e.get("empresa") or e.get("puesto") or e.get("funciones"))
        ]

        # Datos extendidos para empaquetar dentro de customData
        extended_data = {
            "genero": self.genero,
            "fecha_Nacimiento": self.fecha_Nacimiento,
            "nacionalidad": self.nacionalidad,
            "telefono_Alternativo": self.telefono_Alternativo,
            "ciudad": self.ciudad,
            "direccion": self.direccion,
            "grado_Nombre": self.grado_Nombre,
            "carrera": self.carrera,
            "institucion": self.institucion,
            "estado_Estudios": self.estado_Estudios,
            "periodo_Estudio": self.periodo_Estudio,
            "experiencia_Total": self.experiencia_Total,
            "experiencias_Laborales": exps_validas,
            "expectativa_Salarial": self.expectativa_Salarial,
            "disponibilidad": self.disponibilidad,
            "linkedin_Url": self.linkedin_Url
        }
        
        return {
            "tipo_Identificacion": int(self.tipo_Identificacion),
            "identificacion": self.identificacion.strip(),
            "id_Compania": int(job.get("company_id") or job.get("id_Compania") or 0),
            "primer_Nombre": self.primer_Nombre.strip(),
            "segundo_Nombre": self.segundo_Nombre.strip() if self.segundo_Nombre else None,
            "primer_Apellido": self.primer_Apellido.strip(),
            "segundo_Apellido": self.segundo_Apellido.strip() if self.segundo_Apellido else None,
            "nombre_Completo": self.nombre_Completo,
            "comentario": self.generar_comentario_evaluador(),
            "email": self.email.strip(),
            "telefono": self.telefono.strip(),
            "id_GradoAcademico": self.id_GradoAcademico,
            "etiqueta": self.etiqueta or "",
            "id_Requisicion": job.get("id") or job.get("id_Requisicion"),
            "id_Supervisor": None,
            "id_Departamento": job.get("department_id") or job.get("id_Departamento"),
            "apreciacion": self.apreciacion or 0,
            "origen_Solicitante": 1,  # 1 = Externo
            "nombre_Departamento": job.get("department_name") or job.get("nombre_Departamento", ""),
            "nombre_Supervisor": job.get("supervisor_name") or job.get("nombre_Supervisor", ""),
            "ExtraCustomData": custom_fields_json,
            "customData": extended_data
        }
