import cv2

# Coordenadas actuales del ROI
X1, X2 = 20, 620
Y1, Y2 = 65, 415


# Iniciar la cámara (0 cámara predeterminada, 1 para la cámara externa, etc.)
cap = cv2.VideoCapture(0)

print("Iniciando cámara... Presiona la tecla 'q' en la ventana de video para cerrar.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: No se pudo leer la cámara.")
        break

    # 1. Dibujar el rectángulo general del ROI en color verde
    cv2.rectangle(frame, (X1, Y1), (X2, Y2), (0, 255, 0), 2)
    
    # 2. Dibujar una línea ROJA más gruesa en la SALIDA (X2)
    # Acá es donde tiene que coincidir exactamente la punta de la tabla
    cv2.line(frame, (X2, Y1), (X2, Y2), (0, 0, 255), 3)

    # Mostrar la imagen
    cv2.imshow("Alineacion para Offset", frame)

    # Esperar la tecla 'q' para salir
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()