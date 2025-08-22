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
2. Instalar las dependencias:
   
   ```bash
   npm install
3. Configurar las credenciales de Google:
   
   ```bash
   set GOOGLE_APPLICATION_CREDENTIALS=clave.json

## Ejecución

1. Iniciar el servidor:

   ```bash
   npm start

2. Abrir en el navegador el enlace:
   
   ```bash
   http://localhost:3000
3. Se visualizará la interfaz de transcripción en tiempo real.

## Uso
- Presione Iniciar para comenzar la transcripción.

- Seleccione el idioma según el contexto clínico.

- Los datos se reflejarán en el área de texto libre y en el panel estructurado.

- Al finalizar, presione Detener.
