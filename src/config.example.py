# ==========================================
# PLANTILLA DE CONFIGURACIÓN Y CALIBRACIÓN
# ==========================================
# Renombrar este archivo a 'config.py' y completar con los valores
# calibrados en banco para el montaje físico específico de la máquina.

PUERTO_SERIAL = "COM_X"  # Reemplazar por el puerto COM asignado al Arduino UNO en el equipo
BAUDRATE = 115200  # Velocidad de comunicación serial en baudios (debe coincidir con firmware.ino)
INDICE_CAMARA = 0  # Índice de la cámara web USB detectada por OpenCV

# Definición del ROI (Region of Interest) sobre el fotograma de 640x480 px
# Valores neutros a cuadro completo; ajustar en banco para encuadrar la tabla
ROI_Y1 = 0  # Límite superior del recorte en píxeles (borde superior de la tabla)
ROI_Y2 = 480  # Límite inferior del recorte en píxeles (borde inferior de la tabla)
ROI_X1 = 0  # Línea de entrada del ROI en píxeles (borde izquierdo de ingreso de madera)
ROI_X2 = 640  # Línea de salida del ROI en píxeles (punto cero espacial hacia la sierra/láser)

# Umbrales para la detección por visión artificial (calibrar según iluminación del taller)
UMBRAL_OSCURO = 127  # Intensidad máxima (0-255) para binarizar una zona oscura como nudo
UMBRAL_MADERA_PRESENTE = 127  # Brillo promedio mínimo del ROI para confirmar presencia de madera
AREA_MINIMA = 0  # Área mínima en píxeles cuadrados para descartar aserrín y vetas pequeñas

# Relaciones físicas de calibración óptica y odometría mecánica
PIXELES_POR_MM = 1.0  # Valor neutro provisorio (no usar 0.0; calibrar con regla sobre la cinta)
PASOS_POR_MM = 3.4388  # Constante mecánica nominal (800 pasos/rev, poleas 18/28, rodillo de 115.19 mm)

# Parámetros de agrupamiento y márgenes de saneado (criterios de proceso finger joint)
LONGITUD_MINIMA_MM = 100  # Separación mínima en mm entre nudos para no fusionarlos en un solo corte
DISTANCIA_MINIMA_PIXELES = LONGITUD_MINIMA_MM * PIXELES_POR_MM  # Equivalencia en píxeles de la separación mínima

MARGEN_SEGURIDAD_MM = 10  # Margen de madera sana en mm agregado antes y después de cada nudo
MARGEN_SEGURIDAD_PIXELES = MARGEN_SEGURIDAD_MM * PIXELES_POR_MM  # Margen de seguridad traducido a píxeles para el gatillo

# Distancia física desde la línea de salida del ROI (X2) hasta el plano de corte/láser
OFFSET_SIERRA_MM = 1000.0  # Offset nominal en milímetros (ajustar a la distancia real de montaje)

# Conversión directa a pasos del motor (referencia para cálculos y diagnóstico)
OFFSET_SIERRA_PASOS = int(OFFSET_SIERRA_MM * PASOS_POR_MM)  # Pulsos equivalentes al offset físico
MARGEN_SEGURIDAD_PASOS = int(MARGEN_SEGURIDAD_MM * PASOS_POR_MM)  # Pulsos equivalentes al margen de seguridad