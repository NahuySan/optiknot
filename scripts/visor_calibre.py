import cv2

# ==========================================
# CONSTANTES DE CONFIGURACIÓN
# ==========================================
INDICE_CAMARA = 1  # Asegurate de que coincida con la de tu config.py
# Mantenemos las coordenadas de la ROI de tu proyecto
ROI_Y1, ROI_Y2 = 65, 415
ROI_X1, ROI_X2 = 20, 620

# ==========================================
# FUNCIÓN VACÍA PARA LOS SLIDERS
# ==========================================
def nothing(x):
    """Función de callback obligatoria para los trackbars de OpenCV"""
    pass

# ==========================================
# INICIALIZACIÓN DE VENTANAS Y CÁMARA
# ==========================================
# Creamos una ventana nombrada para poder asignarle los controles
cv2.namedWindow('Visor de Calibracion')

# Creamos un slider para ajustar el umbral en tiempo real (0 a 255)
# El valor inicial se lo seteamos en tu constante actual: 80
cv2.createTrackbar('Umbral Oscuro', 'Visor de Calibracion', 80, 255, nothing)
# Slider opcional para el desenfoque Gaussiano (tiene que ser impar)
cv2.createTrackbar('Desenfoque', 'Visor de Calibracion', 5, 21, nothing)

cap = cv2.VideoCapture(INDICE_CAMARA)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Iniciando Visor de Calibración...")
print("Presioná 'q' en la ventana para salir.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error al leer la cámara.")
            break

        # Recortamos la imagen usando tu ROI
        frame_roi = frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
        
        # Convertimos a grises
        gris = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)

        # Leemos los valores actuales de los sliders
        umbral_actual = cv2.getTrackbarPos('Umbral Oscuro', 'Visor de Calibracion')
        desenfoque_actual = cv2.getTrackbarPos('Desenfoque', 'Visor de Calibracion')

        # El tamaño del kernel para GaussianBlur debe ser impar (1, 3, 5, 7...)
        if desenfoque_actual % 2 == 0:
            desenfoque_actual += 1
            # Evitamos que sea menor a 1
            if desenfoque_actual < 1: 
                desenfoque_actual = 1

        # Aplicamos los filtros con los valores en vivo
        desenfoque = cv2.GaussianBlur(gris, (desenfoque_actual, desenfoque_actual), 0)
        _, mascara_binaria = cv2.threshold(desenfoque, umbral_actual, 255, cv2.THRESH_BINARY_INV)

        # Mostramos ambas ventanas: la original con el ROI y cómo está viendo el filtro
        cv2.imshow('Visor de Calibracion', frame_roi)
        cv2.imshow('Mascara Binaria en Vivo', mascara_binaria)

        # Salimos con 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nDetenido por teclado.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Visor cerrado.")