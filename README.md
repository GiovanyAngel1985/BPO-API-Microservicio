# BPO IA Microservicio - Seguros Bolívar

Microservicio REST que **automatiza los 6 pasos críticos** del proceso BPO usando **IA híbrida (LLM + reglas)**. Soporta **4 empresas** con crecimiento escalable.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-blue?logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Llama3.1-orange?logo=groq)](https://groq.com)
[![Python](https://img.shields.io/badge/Python-3.13-green?logo=python)](https://python.org)

## **Características**
**4 empresas** preconfiguradas (Gases del Orinoco, Seguros Bolívar, Mapfre, AXA Colpatria)  
**Validación automática** info mínima requerida  
**Clasificación IA** con Llama 3.1 (Groq)  
**Priorización inteligente** Alta/Media/Baja  
**Decisión automática** GESTION_EXTERNA/RESPUESTA_DIRECTA  
**Simulación** creación casos externos  
**Manejo errores** (empresas no parametrizadas, APIs externas)  
**100% local** - Sin cloud requerido  

## **Instalación (2 min)**

```bash
# 1. Clona y entra
git clone <tu-repo>
cd prueba-tecnica

# 2. Entorno virtual
python -m venv env
# Windows:
env\Scripts\activate
# Linux/Mac:
source env/bin/activate

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura Groq (opcional - ver fallback)
echo GROQ_API_KEY=tu_key > .env
# Regístrate gratis: https://console.groq.com/keys

# 5. Ejecuta
uvicorn main:app --reload --port 8000


# Docs automáticas
 http://localhost:8000/docs