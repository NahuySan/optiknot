import cv2

# Modificá el índice (0, 1, 2) según qué número le asigne Windows a Iriun Webcam
INDICE_CAMARA = 1

ROI_Y1 = 65
ROI_Y2 = 415
ROI_X1 = 20
ROI_X2 = 620

cap = cv2.VideoCapture(INDICE_CAMARA)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer la transmisión.")
        break
    
    # Dibujamos un rectángulo provisorio para simular tu ROI de prueba. 
    # (Ajustá las coordenadas de la ROI de ser necesario para que encuadre tu regla)
    cv2.rectangle(frame, (20, 65), (620, 415), (255, 0, 0), 2) 

    cv2.imshow("Visor de Calibracion - Presiona 'C' para capturar", frame)

    tecla = cv2.waitKey(1) & 0xFF
    
    # Tecla 'C' para tomar la foto y calcular
    if tecla == ord('c'):
        cv2.imwrite("captura_calibracion.png", frame)
        print("Captura guardada como captura_calibracion.png")
        break
    # Tecla 'Q' para salir sin capturar
    elif tecla == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()