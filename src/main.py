import cv2
import time

# ==========================================
# IMPORTACIÓN DE MÓDULOS DEL PROYECTO
# ==========================================
# Importamos todas las constantes físicas y umbrales (config.py)
from config import *
# Importamos la lógica matemática de agrupamiento de cajas (vision.py)
from vision import agrupar_defectos_cercanos
# Importamos las funciones de manejo del puerto serie (com.py)
import com as com

# ==========================================
# VARIABLES DE ESTADO GLOBALES
# ==========================================
# 'bloqueo_lectura_nudo' evita que un mismo nudo dispare el corte múltiples veces
# mientras atraviesa la zona de escaneo de la cámara.
bloqueo_lectura_nudo = False 
estado_actual_motor = "DETENIDO"
ultimo_y_registrado = 0
tiempo_inicio_deteccion = 0.0 
tiempo_congelado = 0.0
timer_activo = False
madera_en_cinta = False
odometria_actual = "0"

# ==========================================
# INICIALIZACIÓN DE HARDWARE
# ==========================================
# Abrimos el puerto COM usando los parámetros definidos en config.py
print("[+] Inicializando comunicación con Arduino...")
arduino = com.inicializar_conexion(PUERTO_SERIAL, 115200)

# Levantamos el stream de video de la cámara USB
print("[+] Inicializando cámara de inspección...")
cap = cv2.VideoCapture(INDICE_CAMARA)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60) # Tasa de refresco alta para no perder nudos a velocidad operativa

# ==========================================
# BUCLE PRINCIPAL DE LA MÁQUINA DE VISIÓN
# ==========================================
try:
    while True:
        # Capturamos el frame actual de la cámara
        ret, frame = cap.read()
        
        # Si perdemos la conexión de video, cortamos el bucle para no procesar basura
        if not ret:
            print("[!] Falla crítica: Pérdida de señal de video.")
            break

        # ---------------------------------------------------------
        # PROCESAMIENTO ÓPTICO Y EXTRACCIÓN DE CARACTERÍSTICAS
        # ---------------------------------------------------------
        # Recortamos la imagen al ROI (Región de Interés) para ahorrar ciclos de CPU
        frame_roi = frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
        
        # Convertimos a escala de grises para detectar por luminancia y no por color (las vetas de madera son oscuras)
        gris = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
        
        # Calculamos la luz promedio para saber si hay madera en la cinta o está vacía
        brillo_promedio = cv2.mean(gris)[0]
        lista_cajas_crudas = []

        # Si el brillo supera el umbral, significa que ingresó madera a la cámara
        if brillo_promedio > UMBRAL_MADERA_PRESENTE:

            # --- LÓGICA DEL SENSOR VIRTUAL ---
            if not madera_en_cinta:
                madera_en_cinta = True  # Marcamos que entró una tabla
                com.enviar_comando_reset_odometria(arduino) # Disparamos el Reset a la placa
                print("[!] BORDE DE INICIO DETECTADO: Odometría reseteada a 0.")            
            
            # Aplicamos un filtro Gaussiano para suavizar las vetas y no confundirlas con nudos
            desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
            
            # Binarizamos la imagen: los nudos (oscuros) pasan a ser blancos y la madera negra
            _, umbral = cv2.threshold(desenfoque, UMBRAL_OSCURO, 255, cv2.THRESH_BINARY_INV)
            
            # Buscamos los bordes de esas manchas blancas
            contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtramos manchas por tamaño (para ignorar polvo o astillas)
            for contorno in contornos:
                area = cv2.contourArea(contorno)
                if area > AREA_MINIMA:
                    # Envolvemos el defecto válido en un rectángulo matemático
                    x, y, w, h = cv2.boundingRect(contorno)
                    lista_cajas_crudas.append((x, y, w, h))
                    
            # Si un nudo se detectó fragmentado, unificamos las cajas cercanas
            cajas_procesadas = agrupar_defectos_cercanos(lista_cajas_crudas, DISTANCIA_MINIMA_PIXELES)
            
            # ---------------------------------------------------------
            # LÓGICA DE RASTREO Y DECISIÓN DE CORTE
            # ---------------------------------------------------------
            if len(cajas_procesadas) > 0:
                # Tomamos el nudo unificado de mayor relevancia
                x_fin, y_fin, w_fin, h_fin = cajas_procesadas[0]
                borde_superior = y_fin
                borde_inferior = y_fin + h_fin
                alto_roi = ROI_Y2 - ROI_Y1
                
                # Definimos márgenes operativos para evitar cortes en el borde de la imagen
                limite_seguridad_inferior = alto_roi - MARGEN_SEGURIDAD_PIXELES
                limite_seguridad_superior = MARGEN_SEGURIDAD_PIXELES
                
                # --- DESBLOQUEO POR DESPLAZAMIENTO GEOMÉTRICO ---
                # Si el nudo ya fue procesado pero avanzó 40 píxeles, liberamos el sistema
                # para estar listos para detectar el siguiente defecto en la tabla.
                if bloqueo_lectura_nudo:
                    if borde_superior < (ultimo_y_registrado - 40):
                        bloqueo_lectura_nudo = False
                    else:
                        ultimo_y_registrado = borde_superior
                
                # --- EVALUACIÓN DE DISPARO ---
                # Verificamos que el nudo esté completamente dentro del margen de seguridad visual
                if borde_inferior < limite_seguridad_inferior and borde_superior > limite_seguridad_superior:
                    
                    # Si no está bloqueado, significa que es la primera vez que vemos este nudo validado
                    if not bloqueo_lectura_nudo:
                        # Bloqueamos inmediatamente para no inundar el puerto serial
                        bloqueo_lectura_nudo = True 
                        ultimo_y_registrado = borde_superior
                        
                        # Iniciamos el contador en pantalla para monitoreo
                        tiempo_inicio_deteccion = time.time()
                        timer_activo = True
                        tiempo_congelado = 0.0
                        
                        # --- CÁLCULO ODOMÉTRICO ---
                        largo_nudo_mm = h_fin / PIXELES_POR_MM
                        # Corte 1: Distancia a la sierra menos el margen de seguridad
                        dist_corte_1_mm = OFFSET_SIERRA_MM - (borde_superior / PIXELES_POR_MM) - MARGEN_SEGURIDAD_MM
                        # Corte 2: Corte 1 + largo del nudo + márgenes a ambos lados
                        dist_corte_2_mm = dist_corte_1_mm + largo_nudo_mm + (MARGEN_SEGURIDAD_MM * 2)
                        
                        # Convertimos las distancias en milímetros a pasos absolutos del motor
                        pasos_corte_1 = int(dist_corte_1_mm * PASOS_POR_MM)
                        pasos_corte_2 = int(dist_corte_2_mm * PASOS_POR_MM)

                        # --- ENVÍO DE DATOS AL ARDUINO ---
                        # Mandamos el comando a la cola FIFO de la placa
                        com.enviar_comando_corte(arduino, pasos_corte_1, pasos_corte_2)
                        print(f"[!] Nudo detectado. Corte frontal: {pasos_corte_1} pasos | Trasero: {pasos_corte_2} pasos")

                        # --- NUEVAS LÍNEAS PARA COMPROBAR EL OFFSET EN CONSOLA ---
                        posicion_camara_mm = borde_superior / PIXELES_POR_MM
                        offset_comprobado = dist_corte_1_mm + posicion_camara_mm + MARGEN_SEGURIDAD_MM
                        print(f"    -> Comprobación Offset: {dist_corte_1_mm:.1f}mm (Faltante) + {posicion_camara_mm:.1f}mm (En ROI) + {MARGEN_SEGURIDAD_MM}mm (Margen) = {offset_comprobado:.1f}mm")
                        
                        # Dibujamos en verde para indicar confirmación de envío
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 255, 0), 3)
                    else:
                        # Si ya lo mandamos a cortar, lo seguimos dibujando en rojo mientras baja
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 0, 255), 3)
                else:
                    # El nudo está en pantalla pero fuera de los márgenes seguros (aún no gatilla)
                    if bloqueo_lectura_nudo:
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 0, 255), 3)
                    else:
                        # Amarillo: Nudo en tránsito, aproximándose al área de gatillo
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 255, 255), 2)
            else:
                # Si no hay cajas válidas procesadas, liberamos el bloqueo para no trabar el ciclo
                bloqueo_lectura_nudo = False
                
        else:
            # Si no hay madera en la cinta (fondo oscuro), reseteamos todos los estados
            bloqueo_lectura_nudo = False
            ultimo_y_registrado = 0

        # ---------------------------------------------------------
        # TRANSMISIÓN SERIAL CONTINUA (Señal de "Keep Alive")
        # ---------------------------------------------------------
        # Si no le avisamos que está avanzando, le mandamos el pulso 'A' al Arduino
        if estado_actual_motor != "AVANZANDO":
            com.enviar_comando_avance(arduino)
            estado_actual_motor = "AVANZANDO"

        # Leemos el buffer de entrada sin bloquear los FPS de la cámara
        if arduino and arduino.in_waiting > 0:
            try:
                linea_serial = arduino.readline().decode('utf-8').strip()
                if linea_serial.startswith("ODOM:"):
                    # Extraemos solo el número de los pasos
                    odometria_actual = linea_serial.split(":")[1]
            except Exception as e:
                # Ignoramos lecturas sucias por ruido en el USB
                pass        

        # ---------------------------------------------------------
        # INTERFAZ GRÁFICA Y DIAGNÓSTICO EN TIEMPO REAL
        # ---------------------------------------------------------
        if timer_activo or tiempo_congelado > 0:
            if timer_activo:
                tiempo_mostrar = time.time() - tiempo_inicio_deteccion
                color_texto = (0, 255, 0)
            else:
                tiempo_mostrar = tiempo_congelado
                color_texto = (0, 0, 255)
                
            texto_timer = f"T: {tiempo_mostrar:.2f} s"
            cv2.putText(frame_roi, texto_timer, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color_texto, 2)

        # Mostramos los pasos absolutos en tiempo real en la pantalla
        cv2.putText(frame_roi, f"Pasos Motor: {odometria_actual}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Dibujamos las coordenadas de las esquinas del ROI para calibración física de la cámara
        alto_roi_px = ROI_Y2 - ROI_Y1
        ancho_roi_px = ROI_X2 - ROI_X1
        color_vertice = (255, 255, 255)
        
        cv2.putText(frame_roi, f"X1, Y1", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_vertice, 1)
        cv2.putText(frame_roi, f"X2, Y1", (ancho_roi_px - 60, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_vertice, 1)
        cv2.putText(frame_roi, f"X1, Y2", (5, alto_roi_px - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_vertice, 1)
        cv2.putText(frame_roi, f"X2, Y2", (ancho_roi_px - 60, alto_roi_px - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_vertice, 1)

        # Renderizamos las ventanas de diagnóstico
        cv2.imshow("Panel de Inspeccion Principal", frame_roi)
        
        if 'umbral' in locals():
            cv2.imshow("Visor de Mascara Binaria", umbral)

        # Escuchamos la tecla 'q' para abortar el programa de forma controlada
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n[!] Cierre solicitado por interfaz gráfica (q).")
            break

# ==========================================
# RUTINA DE EMERGENCIA Y LIMPIEZA DE RECURSOS
# ==========================================
except KeyboardInterrupt:
    print("\n[!] Interrupción manual (Ctrl+C). Deteniendo máquina de forma segura...")

finally:
    # Liberamos la cámara y destruimos ventanas de OpenCV
    cap.release()
    cv2.destroyAllWindows()
    
    # Fundamental: cerramos el puerto COM para no dejar bloqueado al Arduino
    com.cerrar_conexion(arduino)
    print("Recursos liberados. Fin de la ejecución.")