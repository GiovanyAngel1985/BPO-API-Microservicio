import os
from datetime import datetime
from typing import Dict, Any, Tuple
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()
app = FastAPI(title="BPO IA Microservicio")

# Configs por empresa (escalable)
EMPRESAS_CONFIG: Dict[str, Dict] = {
    "GASES DEL ORINOCO": {
        "categorias": ["Incidente técnico", "Falla de equipo", "Consulta de facturación", "Solicitud administrativa"],
        "delegaciones_externas": ["Incidente técnico", "Falla de equipo"]
    },
    "SEGUROS BOLIVAR": {
        "categorias": ["Trámite de póliza", "Siniestro salud", "Consulta médica", "Afiliación nueva"],
        "delegaciones_externas": ["Siniestro salud"]
    },
    "MAPFRE COLOMBIA": {
        "categorias": ["Seguro vehículo", "Accidente carro", "Daños terceros", "Renovación póliza"],
        "delegaciones_externas": ["Accidente carro", "Daños terceros"]
    },
    "AXA COLPATRIA": {
        "categorias": ["Seguro de vida", "Beneficios funerarios", "Pensión", "Invalidez"],
        "delegaciones_externas": ["Seguro de vida", "Beneficios funerarios"]
    }
}

# LLM Groq
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama-3.1-8b-instant",
    temperature=0.1
)

class RequestInput(BaseModel):
    compania: str
    solicitudid: str
    solicituddescripcion: str

class RequestOutput(BaseModel):
    compania: str
    solicitudid: str
    solicitudfecha: str
    solicitudtipo: str
    solicitudprioridad: str
    solicitudidcliente: str | None = None
    solicitudtipoidcliente: str | None = None
    solicitudidplataformaexterna: str | None = None
    proximopaso: str
    justificacion: str
    estado: str = "pendiente"

def validar_info_minima(texto: str) -> bool:
    texto_lower = texto.lower()
    tiene_que_paso = any(palabra in texto_lower for palabra in ["qué", "que", "que paso", "problema", "solicito"])
    tiene_cuando = any(palabra in texto_lower for palabra in ["hace", "hoy", "ayer", "semana", "mes"])
    tiene_que_necesita = any(palabra in texto_lower for palabra in ["necesito", "solicito", "quiero"])
    return tiene_que_paso and (tiene_cuando or tiene_que_necesita)

def clasificar_priorizar(texto: str, compania: str) -> Tuple[str, str, str]:
    config = EMPRESAS_CONFIG.get(compania, {})
    
    prompt = ChatPromptTemplate.from_template(
        """Eres un analista BPO experto. Clasifica esta solicitud:

CLIENTE: {compania}
SOLICITUD: {texto}

CATEGORÍAS POSIBLES: {categorias}

Responde EXACTAMENTE en este formato (sin texto extra):
TIPO|PRIORIDAD|JUSTIFICACION

Ejemplo: Incidente técnico|Alta|Falla técnica que requiere intervención presencial"""
    )
    
    chain = prompt | llm
    response = chain.invoke({
        "compania": compania,
        "texto": texto,
        "categorias": ", ".join(config.get("categorias", []))
    })
    
    # Parseado de respuesta
    contenido = response.content.strip()
    partes = contenido.split("|")
    if len(partes) >= 3:
        return partes[0].strip(), partes[1].strip(), "|".join(partes[2:]).strip()
    else:
        return "Consulta", "Media", "Clasificación automática por defecto"

def extraer_id_cliente(texto: str) -> Tuple[str | None, str | None]:
    import re
    # Buscar la cédula colombiana (8-10 dígitos)
    cedula_match = re.search(r'\b\d{8,10}\b', texto)
    if cedula_match:
        return "CC", cedula_match.group(0)
    return None, None

def decidir_paso(tipo: str, compania: str) -> Tuple[str, str | None]:
    config = EMPRESAS_CONFIG.get(compania, {})
    if tipo.lower() in [d.lower() for d in config.get("delegaciones_externas", [])]:
        id_externo = f"ID{compania[:3].upper()}{len(compania)}789"
        return "GESTION_EXTERNA", id_externo
    return "RESPUESTA_DIRECTA", None

@app.post("/process_request", response_model=RequestOutput)
async def process_request(req: RequestInput):
    if req.compania not in EMPRESAS_CONFIG:
        raise HTTPException(status_code=400, detail="Empresa no parametrizada")
    
    # 1. Validar información mínima
    if not validar_info_minima(req.solicituddescripcion):
        return RequestOutput(
            compania=req.compania,
            solicitudid=req.solicitudid,
            solicitudfecha=datetime.now().strftime("%Y-%m-%d"),
            solicitudtipo="",
            solicitudprioridad="",
            proximopaso="CIERRE_POR_INFORMACION_INSUFICIENTE",
            justificacion="Información incompleta o faltante"
        )
    
    # 2-3. Clasificar y priorizar la información
    tipo, prioridad, justificacion = clasificar_priorizar(req.solicituddescripcion, req.compania)
    
    # 4. Extraer el ID cliente
    tipo_doc, num_doc = extraer_id_cliente(req.solicituddescripcion)
    
    # 5. Decisión del siguiente paso
    paso, id_externo = decidir_paso(tipo, req.compania)
    
    return RequestOutput(
        compania=req.compania,
        solicitudid=req.solicitudid,
        solicitudfecha=datetime.now().strftime("%Y-%m-%d"),
        solicitudtipo=tipo,
        solicitudprioridad=prioridad,
        solicitudidcliente=tipo_doc,
        solicitudtipoidcliente=num_doc,
        solicitudidplataformaexterna=id_externo,
        proximopaso=paso,
        justificacion=justificacion
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
