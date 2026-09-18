import cv2
import serial
import time

# ==========================================
# CONSTANTES Y CALIBRACIÓN DEL SISTEMA
# ==========================================
# Puerto serie asignado a la placa Arduino (Ajustar según el Administrador de Dispositivos).
PUERTO_SERIAL = "COM4"
# Índice de hardware de la cámara (0 para webcam integrada, 1 para USB externa como PS3 Eye).
INDICE_CAMARA = 1

# Coordenadas provisionales para el recorte de la Región de Interés (ROI).
# Deben ajustarse empíricamente para aislar solo la cinta transportadora.
ROI_Y1 = 115
ROI_Y2 = 355
ROI_X1 = 70
ROI_X2 = 560

# Valor del umbral de intensidad para la binarización (detección de defectos oscuros).
UMBRAL_OSCURO = 80
# Valor mínimo de intensidad promedio para validar que la tabla de pino ingresó a la ROI.
UMBRAL_MADERA_PRESENTE = 100 
# Superficie mínima del polígono en píxeles para catalogarlo como defecto estructural.
AREA_MINIMA = 500

# Constante de conversión espacial de píxeles a milímetros físicos (Requiere calibración con regla).
PIXELES_POR_MM = 2.37
# Tiempo de pausa (en segundos) para dar margen a la actuación de los cilindros neumáticos.
TIEMPO_CILINDROS = 4.0

# Longitud mínima física de agrupación para nudos cercanos.
LONGITUD_MINIMA_MM = 100
# Conversión de la longitud mínima física a píxeles para el análisis óptico.
DISTANCIA_MINIMA_PIXELES = LONGITUD_MINIMA_MM * PIXELES_POR_MM

# --- MÁRGENES Y DISTANCIAS DE SEGURIDAD FÍSICA ---
# Distancia mínima (en milímetros) desde los extremos del cuadro de visión donde la sierra puede operar sin riesgo.
MARGEN_SEGURIDAD_MM = 10 
# Conversión del margen de seguridad físico a su equivalente en píxeles.
MARGEN_SEGURIDAD_PIXELES = MARGEN_SEGURIDAD_MM * PIXELES_POR_MM

# --- CALIBRACIÓN DE OFFSET MECÁNICO ---
# Distancia física (en mm) medida sobre la cinta transportadora desde la línea inferior del ROI hasta la guillotina.
OFFSET_SIERRA_MM = 600.0


# ==========================================
# FUNCIONES DE PROCESAMIENTO GEOMÉTRICO
# ==========================================
# Definición de la función que recibe la lista de cajas y la distancia de tolerancia.
def agrupar_defectos_cercanos(cajas, distancia_minima):
    # Condicional de escape: si no hay cajas en la lista, retorna una lista vacía.
    if not cajas: return []
    
    # Ordena la lista de cajas basándose en la coordenada Y (de arriba hacia abajo en la imagen).
    cajas.sort(key=lambda b: b[1])
    
    # Inicializa la lista de cajas agrupadas utilizando la primera caja detectada como base.
    cajas_agrupadas = [cajas[0]]
    
    # Bucle que itera sobre las cajas restantes a partir de la segunda posición.
    for caja_actual in cajas[1:]:
        # Extrae la última caja que se guardó en la lista de agrupadas (la más baja hasta el momento).
        caja_anterior = cajas_agrupadas[-1]
        
        # Desempaqueta las coordenadas y dimensiones de la caja anterior.
        x_ant, y_ant, w_ant, h_ant = caja_anterior
        # Desempaqueta las coordenadas y dimensiones de la caja actual que se está evaluando.
        x_act, y_act, w_act, h_act = caja_actual
        
        # Calcula la distancia vertical vacía entre el borde inferior de la caja anterior y el borde superior de la actual.
        distancia_y = y_act - (y_ant + h_ant)
        
        # Evalúa si la distancia calculada es menor al margen de seguridad estipulado para fusionar.
        if distancia_y < distancia_minima:
            # FUSIÓN DE CAJAS: Determina la coordenada Y superior más alta (menor valor numérico).
            nuevo_y = min(y_ant, y_act)
            # Calcula la nueva altura total restando la coordenada Y inicial al punto más bajo alcanzado por ambas cajas.
            nuevo_h = max(y_ant + h_ant, y_act + h_act) - nuevo_y
            # Determina la coordenada X más desplazada hacia la izquierda por seguridad transversal.
            nuevo_x = min(x_ant, x_act)
            # Calcula el nuevo ancho total abarcando los extremos derechos de ambas cajas.
            nuevo_w = max(x_ant + w_ant, x_act + w_act) - nuevo_x
            
            # Reemplaza la última caja en la lista con esta nueva macro-caja fusionada.
            cajas_agrupadas[-1] = (nuevo_x, nuevo_y, nuevo_w, nuevo_h)
        else:
            # Si la distancia es amplia, añade la caja actual como un defecto independiente.
            cajas_agrupadas.append(caja_actual)
            
    # Retorna la lista final con las cajas ya procesadas y fusionadas si correspondía.
    return cajas_agrupadas


# ==========================================
# INICIALIZACIÓN DE HARDWARE
# ==========================================
try:
    # Apertura del puerto serie a 9600 baudios.
    arduino = serial.Serial(PUERTO_SERIAL, 9600, timeout=1)
    # Pausa de seguridad para permitir la inicialización del bootloader del microcontrolador.
    time.sleep(2)
    print("Comunicación serial establecida.")
except Exception as e:
    # Advertencia en caso de falla de conexión por protocolo USB.
    print(f"Error de hardware: No se pudo abrir el puerto serie. Detalle: {e}")

# Instanciación de la cámara mediante el módulo de captura de OpenCV.
cap = cv2.VideoCapture(INDICE_CAMARA)
# Ajuste forzado de la resolución horizontal para estandarizar la captura.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# Ajuste forzado de la resolución vertical para mantener la relación de aspecto.
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# Ajuste de la tasa de fotogramas a 60 FPS para captura industrial de alta velocidad.
cap.set(cv2.CAP_PROP_FPS, 60)

# Declaración de la variable global de estado para evitar la saturación del buffer serial.
estado_actual_motor = "DETENIDO"


# ==========================================
# BUCLE PRINCIPAL DE MÁQUINA
# ==========================================
while True:
    # Lectura secuencial del fotograma desde el buffer de video.
    ret, frame = cap.read()
    
    # Comprobación de la integridad del flujo de datos de la cámara.
    if not ret:
        # Emisión de mensaje de error por consola ante un corte en la señal.
        print("Falla crítica: Pérdida de señal de video.")
        # Ruptura forzada del bucle principal para detener la máquina.
        break

    # ==========================================
    # PREPROCESAMIENTO Y VALIDACIÓN DE PRESENCIA
    # ==========================================
    # Recorte matricial de la imagen para aislar estrictamente la cinta transportadora (ROI).
    frame_roi = frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
    
    # Conversión del espacio de color BGR a escala de grises para análisis de luminosidad.
    gris = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
    
    # Cálculo del nivel de brillo promedio en toda la extensión de la Región de Interés.
    brillo_promedio = cv2.mean(gris)[0]
    
    # Declaración de la bandera de estado para la orden de corte en el ciclo actual.
    defecto_detectado = False
    
    # Inicialización de la lista temporal destinada a almacenar las coordenadas de los nudos identificados.
    lista_cajas_crudas = []
    
    # Inicialización de las variables de distancia en cero por defecto.
    distancia_corte_1 = 0
    distancia_corte_2 = 0

    # Evaluación principal: comprueba si la luminosidad supera el umbral, indicando que hay madera presente.
    if brillo_promedio > UMBRAL_MADERA_PRESENTE:
        
        # HAY MADERA: Ejecución del pipeline de filtrado óptico.
        # Aplicación de filtro gaussiano para difuminar imperfecciones menores y aserrín.
        desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)
        
        # Binarización invertida para aislar las zonas oscuras de los defectos convirtiéndolas a pixeles blancos.
        _, umbral = cv2.threshold(desenfoque, UMBRAL_OSCURO, 255, cv2.THRESH_BINARY_INV)
        
        # Detección y extracción topológica de los polígonos generados en la máscara binaria.
        contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Iteración secuencial sobre cada contorno hallado en la imagen.
        for contorno in contornos:
            # Cálculo matemático de la superficie cubierta por el polígono.
            area = cv2.contourArea(contorno)
            
            # Filtro geométrico: descarta los puntos oscuros cuya área sea irrelevante para la estructura.
            if area > AREA_MINIMA:
                # Extracción de las coordenadas X, Y, ancho y alto de la caja delimitadora ortogonal.
                x, y, w, h = cv2.boundingRect(contorno)
                # Almacenamiento de la tupla de datos en la lista de defectos en crudo.
                lista_cajas_crudas.append((x, y, w, h))
                
        # Procesamiento de consolidación: unifica defectos contiguos mediante la función geométrica.
        cajas_procesadas = agrupar_defectos_cercanos(lista_cajas_crudas, DISTANCIA_MINIMA_PIXELES)
        
        # Verificación final: constata si quedaron defectos validados tras el proceso de agrupación.
        if len(cajas_procesadas) > 0:
            
            # Extracción prioritaria de los datos correspondientes a la primera caja detectada (la más adelantada).
            x_fin, y_fin, w_fin, h_fin = cajas_procesadas[0]
            
            # Definición geométrica de los extremos superior e inferior del nudo.
            borde_superior = y_fin
            borde_inferior = y_fin + h_fin
            
            # Cálculo de la altura total de la zona de visión en píxeles.
            alto_roi = ROI_Y2 - ROI_Y1
            
            # ==========================================
            # DECISIÓN LÓGICA: GATILLO POR INGRESO COMPLETO
            # ==========================================
            # Define la línea virtual que el borde inferior del defecto debe atravesar para gatillar.
            limite_seguridad_inferior = alto_roi - MARGEN_SEGURIDAD_PIXELES
            # Define el margen superior para evitar errores de cálculo en el ingreso.
            limite_seguridad_superior = MARGEN_SEGURIDAD_PIXELES
            
            # Validación cinemática: evalúa si el nudo completo ingresó a la zona segura de medición.
            if borde_inferior < limite_seguridad_inferior and borde_superior > limite_seguridad_superior:
                
                # SÍ: El defecto ingresó completamente. Se autoriza el cálculo de las distancias de encapsulamiento.
                defecto_detectado = True
                
                # Conversión de la longitud total del defecto de píxeles a unidades métricas (milímetros).
                largo_nudo_mm = h_fin / PIXELES_POR_MM
                
                # Cálculo de la distancia real para el primer corte (frontal), restando el margen de seguridad.
                distancia_corte_1 = OFFSET_SIERRA_MM - (borde_superior / PIXELES_POR_MM) - MARGEN_SEGURIDAD_MM
                
                # Cálculo de la distancia para el segundo corte (trasero) para amputar el segmento completo.
                distancia_corte_2 = largo_nudo_mm + (MARGEN_SEGURIDAD_MM * 2)

                # Dibujo del perímetro de delimitación final (en color verde) para indicar que el gatillo fue accionado.
                cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 255, 0), 3)
                
            else:
                # NO: El defecto está visible pero su extremo inferior aún no cruzó la línea de confirmación.
                defecto_detectado = False
                
                # Dibujo del perímetro en color amarillo para indicar que el defecto está en seguimiento óptico previo al disparo.
                cv2.rectangle(frame_roi, (x_fin, y_fin), (x_fin + w_fin, borde_inferior), (0, 255, 255), 2)
                
    else:
        # NO HAY MADERA: La región de análisis se encuentra despejada.
        # Bypass algorítmico: se evita el procesamiento óptico para ahorrar recursos de CPU.
        pass


# ==========================================
    # LÓGICA DE CONTROL Y TRANSMISIÓN SERIAL
    # ==========================================
    if defecto_detectado:
        estado_actual_motor = "CORTANDO"
        print(f"\n[!] DEFECTO CONFIRMADO - Iniciando secuencia macro de encapsulamiento")
        
        # Estructuración de la trama compuesta: Distancia 1 y Distancia 2 separadas por pipe.
        trama_macro = f"C:{distancia_corte_1:.2f}|{distancia_corte_2:.2f}\n"
        arduino.write(trama_macro.encode())
        print(f"TX Secuencia Completa: {trama_macro.strip()}")
        
        # --- CÁLCULO DE TIEMPO DE BLOQUEO DINÁMICO ---
        # 1. Tiempo de posicionamiento: Distancia total * 10 pasos/mm * 1.6 milisegundos por paso.
        tiempo_motor_segundos = (distancia_corte_1 + distancia_corte_2) * 10.0 * 0.0016
        # 2. Tiempo neumático: 4 segundos de solapamiento por corte (8 segundos totales).
        tiempo_neumatico_segundos = 8.0 
        
        # Sumatoria total con medio segundo adicional de margen de seguridad lógico.
        tiempo_total_espera = tiempo_motor_segundos + tiempo_neumatico_segundos + 0.5
        
        # Bloqueo estricto del hilo de video mientras la máquina ejecuta el proceso físico.
        time.sleep(tiempo_total_espera)
        
        # Vaciado del buffer de la cámara para retomar el análisis en tiempo real.
        for _ in range(5):
            cap.grab()
            
    else:
        if estado_actual_motor != "AVANZANDO":
            trama_serial = "A\n"
            arduino.write(trama_serial.encode())
            estado_actual_motor = "AVANZANDO"
            print("TX: Reanudando tracción continua (A)")

            
    # ==========================================
    # INTERFAZ DE MONITOREO Y FINALIZACIÓN
    # ==========================================
    # Proyección gráfica del entorno de análisis primario con los marcadores superpuestos.
    cv2.imshow("Panel de Inspeccion Principal", frame_roi)
    
    # Comprobación de existencia en memoria de la variable binaria (prevención de excepciones si la cinta arranca vacía).
    if 'umbral' in locals():
        # Despliegue de la capa de umbralización para calibración óptica en tiempo real.
        cv2.imshow("Visor de Mascara Binaria", umbral)

    # Detección de interrupción por teclado leyendo el evento 'q' (1 milisegundo de espera).
    if cv2.waitKey(1) & 0xFF == ord('q'):
        # Ruptura del ciclo infinito para iniciar el protocolo de apagado del software.
        break

# ==========================================
# LIMPIEZA DE RECURSOS (CLEANUP)
# ==========================================
# Liberación lógica del puerto USB asociado al sensor.
cap.release()
# Cierre forzado y liberación de memoria de las ventanas gráficas de la API OpenCV.
cv2.destroyAllWindows()
# Cierre seguro del protocolo de comunicación serial para evitar bloqueos del puerto COM.
arduino.close()