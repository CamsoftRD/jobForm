from dataclasses import dataclass
from typing import Optional

@dataclass
class GradoModel:
    codigo: int
    nombre: str
    ind_Estado: int
    nombre_Estado: str
    customData: Optional[dict] = None
    customData2: Optional[dict] = None

