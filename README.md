# MAHORAGA
## Sistema Multiagente de Ciberdefensa

MAHORAGA es una arquitectura multiagente de ciberdefensa defensiva implementada sobre TinyClaw v2.0.0. El sistema procesa alertas de seguridad a traves de un pipeline de agentes de IA especializados.

## Pipeline de agentes

Oracle (Orquestador) -> SENTINEL (Triage) -> ATLAS (MITRE ATT&CK) -> AEGIS (Respuesta)

## Agentes

| Agente   | Rol |
|----------|-----|
| Oracle   | Orquestador -- coordina el pipeline y sintetiza resultados |
| SENTINEL | Triage -- extrae IOCs y asigna severidad |
| ATLAS    | Correlacion MITRE ATT&CK -- mapea indicadores a tacticas |
| AEGIS    | Asesor de respuesta -- genera plan sin ejecutar acciones |

## Stack de seguridad

- Suricata -- IDS/IPS para deteccion de trafico malicioso
- Wazuh -- SIEM para correlacion de logs
- Osquery -- Monitoreo del sistema operativo
- TinyClaw v2.0.0 -- Motor de agentes de IA

## Estructura del proyecto

mahoraga/
- seeds/                   # Definicion de personalidad de cada agente
- middleware/               # Normalizacion de alertas al schema SENTINEL
- mahoraga_suricata.py      # Normalizador Suricata (funcional)
- escribir_agents_md.py     # Script de instalacion de seeds

## Requisitos

- Pop!_OS / Ubuntu 22.04+
- Bun runtime
- Python 3.10+
- TinyClaw v2.0.0
- Suricata 6.0+
- API key de Google AI Studio (Gemini 2.0 Flash)

## Equipo

Proyecto de tesis -- Ingenieria en Ciberseguridad | Mayo 2026
