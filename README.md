# Sistema Automático de Saneado de Madera (Visión Artificial)

Este repositorio contiene el código fuente para una máquina saneadora de madera automatizada. El sistema utiliza visión computacional (OpenCV) para detectar defectos (nudos) en tiempo real sobre una cinta transportadora, y se comunica vía puerto serie con un microcontrolador (Arduino) para sincronizar el avance de los motores paso a paso y el accionamiento neumático de la sierra.

## Características Principales

- **Visión Computacional:** Procesamiento de fotogramas a 60 FPS mediante filtrado gaussiano, binarización y análisis de contornos para aislar nudos oscuros sobre la madera.
- **Lógica de Agrupamiento:** Algoritmo geométrico propio para fusionar defectos cercanos o fragmentados (`agrupar_defectos_cercanos`), evitando cortes redundantes.
- **Rastreo Espacial:** Cálculo de odometría basado en la conversión de píxeles a milímetros y compensación de distancia (offset) entre la cámara y la sierra (600 mm).
- **Comunicación Asíncrona:** Protocolo serial custom (tramas `Q:` para cortes y `A` para avance continuo) para orquestar la secuencia de los actuadores sin bloquear el bucle de video.

## Estructura del Repositorio

```text
proyecto_saneadora/
├── firmware/                  # Código fuente para el microcontrolador (.ino)
├── src/                       # Módulos principales del sistema (Python)
│   ├── main.py                # Bucle de orquestación (Visión + Serial)
│   ├── vision.py              # Funciones de procesamiento geométrico
│   ├── comunicacion.py        # Interfaz de control vía PySerial
│   └── config.py              # Constantes físicas, umbrales y calibración
├── scripts/                   # Herramientas de diagnóstico y mantenimiento
│   ├── calibre.py             # Script para cálculo de escala (píxeles/mm)
│   └── visor.py               # Panel de control con sliders para ajustar umbrales en vivo
├── docs/                      # Diagramas de flujo, unifilares y documentación del proyecto
├── .gitignore                 # Exclusión de entornos virtuales y archivos temporales
└── requirements.txt           # Dependencias del proyecto
