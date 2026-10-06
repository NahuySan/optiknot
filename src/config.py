# ==========================================
# CONSTANTES Y CALIBRACIÓN DEL SISTEMA
# ==========================================

PUERTO_SERIAL = "COM4"
BAUDRATE = 115200
INDICE_CAMARA = 1

# Definición del ROI (Region of Interest)
ROI_Y1 = 65
ROI_Y2 = 415
ROI_X1 = 20
ROI_X2 = 620

# Umbrales para la detección por visión artificial
UMBRAL_OSCURO = 80

UMBRAL_MADERA_PRESENTE = 100 
AREA_MINIMA = 500

# Relaciones físicas
PIXELES_POR_MM = 2.37
PASOS_POR_MM = 5.093

# Parámetros de la madera y de seguridad
LONGITUD_MINIMA_MM = 100
DISTANCIA_MINIMA_PIXELES = LONGITUD_MINIMA_MM * PIXELES_POR_MM

MARGEN_SEGURIDAD_MM = 10 
MARGEN_SEGURIDAD_PIXELES = MARGEN_SEGURIDAD_MM * PIXELES_POR_MM

# Distancia de la cámara a la sierra
OFFSET_SIERRA_MM = 600.0

# Conversión de distancias a pasos del motor
OFFSET_SIERRA_PASOS = int(OFFSET_SIERRA_MM * PASOS_POR_MM)
MARGEN_SEGURIDAD_PASOS = int(MARGEN_SEGURIDAD_MM * PASOS_POR_MM)