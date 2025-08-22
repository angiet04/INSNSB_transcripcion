# INSNSB Transcripción

Este proyecto implementa un sistema de transcripción de voz a texto en tiempo real utilizando **Google Speech-to-Text API**.  
El objetivo es facilitar la documentación estructurada de historias clínicas neurológicas mediante una interfaz web interactiva.

---

## Características

- Transcripción en tiempo real desde el micrófono.
- Panel estructurado para capturar:
  - Datos y signos vitales: edad, sexo, peso, talla, TA, FC, FR, temperatura, saturación.
  - Fuerza muscular por grupos (miembro superior e inferior).
  - Examen neurológico: pupilas, pares craneales, tono, reflejos, sensibilidad, coordinación, marcha y signos meníngeos.
- Comandos de voz básicos: pausar y continuar.
- Exportación y limpieza del texto transcrito.
- Interfaz web responsiva y de fácil uso.

---

## Requisitos

- Node.js (versión 14 o superior).
- Cuenta en Google Cloud con **Speech-to-Text API** habilitada.
- Archivo de credenciales JSON de Google Cloud.

---

## Instalación

1. Clonar este repositorio:

   ```bash
   git clone https://github.com/angiet04/INSNSB_transcripcion.git
   cd INSNSB_transcripcion
