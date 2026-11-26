# Sistema Automático de Saneado de Madera (Visión Artificial)

Prototipo funcional de una máquina saneadora de nudos para finger joint (E.P.E.T. N°7, 2026). El sistema emplea visión artificial en tiempo real (Python / OpenCV) para detectar defectos estructurales sobre una cinta transportadora y opera en arquitectura descentralizada junto a un microcontrolador Arduino UNO para el control cinemático en lazo abierto y la sincronización de corte.

## Características Principales

- **Visión Artificial y HMI Desacoplada:** Procesamiento de fotogramas (`640×480 @ 60 fps`) sobre una Región de Interés (ROI) con aplanado a escala de grises, filtro Gaussiano, binarización y filtrado por área mínima, ejecutado en un hilo secundario independiente de la interfaz gráfica (`CustomTkinter`).
- **Agrupamiento Geométrico en Eje Horizontal (`X1 → X2`):** Algoritmo propio (`agrupar_defectos_cercanos`) para unificar defectos próximos o fragmentados dentro del largo mínimo útil, evitando cortes redundantes.
- **Odometría en Lazo Abierto y Rampas Dinámicas:** Transmisión mediante motor paso a paso bipolar Varitel, driver industrial R.T.A. X-PLUS (220V AC, 1/4 de micropaso, `800 pasos/rev`), poleas dentadas HTD `18/28` (relación `1.56:1`) y rodillo tractor de `Ø 115,19 mm` (`3,4388 pasos/mm`), con offset físico de `1000 mm` y perfiles de aceleración trapezoidales/triangulares en firmware.
- **Comunicación Serial Bidireccional (`115200 baudios`):** Protocolo asíncrono no bloqueante con cola FIFO circular en Arduino: transmisión de marcha (`A`), reinicio de odometría por nueva tabla (`R`), coordenadas de corte (`Q:p1|p2`) y recepción de telemetría (`ODOM:xx`).
- **Actuación Modular:** Arquitectura prevista para sistema neumático de 24V DC (pisón superior y sierra inferior ascendente con descarte por gravedad), validada en etapa de prototipo mediante marcador láser de 5 mW (640 nm) comandado por relé.

## Estructura del Repositorio

```text
saneadora/
├── firmware/                  # Firmware modular en C++ para Arduino UNO
│   ├── firmware.ino           # Configuración de pines, FIFO y bucle principal
│   ├── com.ino                # Parseo serial ('A', 'R', 'Q:') y telemetría
│   ├── odo_motor.ino          # Control de rampas dinámicas y odometría
│   └── neumatica.ino          # Máquina de estados no bloqueante (láser / neumática)
├── src/                       # Software de visión artificial y HMI (Python)
│   ├── main.py                # Orquestación multihilo (HMI + visión + serial)
│   ├── vision.py              # Agrupamiento geométrico de defectos en eje X
│   ├── com.py                 # Gestión de puerto serie vía PySerial
│   └── config.example.py      # Constantes de calibración, ROI y umbrales
├── calib/                     # Utilidades de calibración óptica y pruebas de banco
├── docs/                      # Planos mecánicos, unifilares y diagramas de flujo (SVG/PNG)
├── .gitignore                 # Exclusión de entornos virtuales y compilados temporales
├── LICENSE                    # Licencia
└── README.md                  # Documentación general del repositorio