import cv2  # Biblioteca OpenCV para captura y procesamiento de imágenes
import time  # Módulo para gestionar pausas y control de tiempos
import tkinter as tk  # Tkinter base para renderizar el frame de video sin parpadeos
import customtkinter as ctk  # Interfaz gráfica moderna para el panel HMI
from PIL import Image, ImageTk  # Conversión de matrices OpenCV a imágenes compatibles con Tkinter
import threading  # Ejecución del procesamiento de visión en un hilo secundario

# ==========================================
# IMPORTACIÓN DE MÓDULOS DEL PROYECTO
# ==========================================
from config import *  # Importamos todas las constantes de calibración y puertos desde config.py
from vision import agrupar_defectos_cercanos  # Importamos la función de agrupamiento horizontal de nudos
import com as com  # Importamos el módulo de comunicación serial con Arduino

# ==========================================
# VARIABLES DE ESTADO GLOBALES
# ==========================================
bloqueo_lectura_nudo = False  # Bandera para evitar enviar el mismo nudo más de una vez
estado_actual_motor = "DETENIDO"  # Estado lógico del avance comandado al Arduino
ultimo_x_registrado = 0  # Última coordenada horizontal X conocida del nudo bloqueado
madera_en_cinta = False  # Bandera de presencia física de un listón bajo la cámara
odometria_actual = "0"  # Último valor de pasos recibido por telemetría desde Arduino
nudos_totales = 0  # Contador acumulado de nudos enviados a la cola FIFO
ejecutando_vision = True  # Bandera de control para detener limpiamente el hilo de visión al cerrar

# ==========================================
# INICIALIZACIÓN DE HARDWARE
# ==========================================
print("[+] Inicializando comunicación con Arduino...")  # Informamos inicio de conexión serial por consola
arduino = com.inicializar_conexion(PUERTO_SERIAL, BAUDRATE)  # Abrimos el puerto serie usando el baudrate de config.py

print("[+] Inicializando cámara de inspección...")  # Informamos apertura de la cámara por consola
cap = cv2.VideoCapture(INDICE_CAMARA)  # Instanciamos la captura de video en el índice configurado
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Fijamos el ancho de captura en 640 píxeles
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Fijamos el alto de captura en 480 píxeles
cap.set(cv2.CAP_PROP_FPS, 60)  # Solicitamos una tasa de captura objetivo de 60 cuadros por segundo

# ==========================================
# CONFIGURACIÓN DE LA INTERFAZ GRÁFICA
# ==========================================
ctk.set_appearance_mode("Dark")  # Definimos el tema visual oscuro para la HMI
ctk.set_default_color_theme("blue")  # Definimos la paleta de acento azul para controles

app = ctk.CTk()  # Creamos la ventana principal de CustomTkinter
app.title("Saneadora HMI - Control Industrial")  # Asignamos el título de la ventana
app.geometry("1000x600")  # Establecemos las dimensiones iniciales de la ventana

# --- FRAME IZQUIERDO: VIDEO ---
frame_video = ctk.CTkFrame(app, width=640, height=480)  # Contenedor izquierdo reservado para el stream de video
frame_video.pack(side="left", padx=20, pady=20)  # Posicionamos el contenedor de video a la izquierda

lbl_video = tk.Label(frame_video, bg="#242424")  # Label estándar de Tkinter para refresco rápido de video
lbl_video.pack()  # Empaquetamos el visor dentro de su contenedor

# --- FRAME DERECHO: CONTROLES ---
frame_controles = ctk.CTkFrame(app, width=300)  # Contenedor derecho para sliders y telemetría
frame_controles.pack(side="right", fill="y", padx=20, pady=20)  # Posicionamos el panel de control a la derecha

ctk.CTkLabel(frame_controles, text="PARÁMETROS DE VISIÓN", font=("Arial", 16, "bold")).pack(pady=10)  # Título del panel

# Variables reactivas de la interfaz inicializadas con los valores de config.py
var_umbral = ctk.IntVar(value=UMBRAL_OSCURO)  # Variable enlazada al slider de umbral de binarización
var_roi_y1 = ctk.IntVar(value=ROI_Y1)  # Variable enlazada al borde superior del ROI (ancho de tabla)
var_roi_y2 = ctk.IntVar(value=ROI_Y2)  # Variable enlazada al borde inferior del ROI (ancho de tabla)

# Slider Umbral
ctk.CTkLabel(frame_controles, text="Sensibilidad (Umbral Oscuro):").pack(pady=(10, 0))  # Etiqueta descriptiva del umbral
slider_umbral = ctk.CTkSlider(frame_controles, from_=0, to=255, variable=var_umbral)  # Control deslizante de 0 a 255
slider_umbral.pack(pady=5)  # Empaquetamos el slider de umbral
lbl_val_umbral = ctk.CTkLabel(frame_controles, text=str(var_umbral.get()))  # Etiqueta con el valor numérico actual
lbl_val_umbral.pack()  # Empaquetamos el indicador numérico

# Slider ROI Y1 (Borde Superior de la tabla)
ctk.CTkLabel(frame_controles, text="ROI Borde Superior (Y1):").pack(pady=(10, 0))  # Etiqueta descriptiva de Y1
slider_y1 = ctk.CTkSlider(frame_controles, from_=0, to=240, variable=var_roi_y1)  # Control deslizante para Y1
slider_y1.pack(pady=5)  # Empaquetamos el slider Y1
lbl_val_y1 = ctk.CTkLabel(frame_controles, text=str(var_roi_y1.get()))  # Indicador numérico de Y1
lbl_val_y1.pack()  # Empaquetamos el indicador de Y1

# Slider ROI Y2 (Borde Inferior de la tabla)
ctk.CTkLabel(frame_controles, text="ROI Borde Inferior (Y2):").pack(pady=(10, 0))  # Etiqueta descriptiva de Y2
slider_y2 = ctk.CTkSlider(frame_controles, from_=241, to=480, variable=var_roi_y2)  # Control deslizante para Y2
slider_y2.pack(pady=5)  # Empaquetamos el slider Y2
lbl_val_y2 = ctk.CTkLabel(frame_controles, text=str(var_roi_y2.get()))  # Indicador numérico de Y2
lbl_val_y2.pack()  # Empaquetamos el indicador de Y2

# Panel de Telemetría
frame_telemetria = ctk.CTkFrame(frame_controles, fg_color="gray20")  # Subpanel oscuro para métricas en vivo
frame_telemetria.pack(fill="x", pady=20)  # Expandimos el subpanel al ancho disponible
ctk.CTkLabel(frame_telemetria, text="TELEMETRÍA", font=("Arial", 14, "bold")).pack(pady=5)  # Título de telemetría
lbl_telemetria = ctk.CTkLabel(frame_telemetria, text=f"Nudos Totales: {nudos_totales}\nPasos: 0", justify="left")  # Texto dinámico
lbl_telemetria.pack(pady=5)  # Empaquetamos la etiqueta de telemetría

def actualizar_etiquetas(valor):  # Callback ejecutado cuando el usuario mueve cualquiera de los sliders
    lbl_val_umbral.configure(text=str(var_umbral.get()))  # Refrescamos el número mostrado para el umbral
    lbl_val_y1.configure(text=str(var_roi_y1.get()))  # Refrescamos el número mostrado para Y1
    lbl_val_y2.configure(text=str(var_roi_y2.get()))  # Refrescamos el número mostrado para Y2

slider_umbral.configure(command=actualizar_etiquetas)  # Vinculamos el slider de umbral al callback
slider_y1.configure(command=actualizar_etiquetas)  # Vinculamos el slider Y1 al callback
slider_y2.configure(command=actualizar_etiquetas)  # Vinculamos el slider Y2 al callback


# ==========================================
# BUCLE PRINCIPAL DE VISIÓN (HILO SECUNDARIO)
# ==========================================
def procesar_video():  # Función que corre en segundo plano para capturar, procesar y comunicarse con Arduino
    global bloqueo_lectura_nudo, ultimo_x_registrado, madera_en_cinta  # Declaramos acceso a banderas de detección
    global odometria_actual, estado_actual_motor, nudos_totales, ejecutando_vision  # Declaramos acceso a telemetría y control

    buffer_serial = ""  # Buffer local para ensamblar líneas completas de telemetría sin cortes parciales

    def renderizar_gui(img_pil, nudos, pasos):  # Función ejecutada únicamente en el hilo principal mediante app.after()
        if not ejecutando_vision:  # Evitamos tocar widgets si la ventana ya inició su cierre
            return  # Salimos sin actualizar la interfaz
        img_tk = ImageTk.PhotoImage(image=img_pil)  # Instanciamos ImageTk de forma segura en el hilo principal de Tkinter
        lbl_video.configure(image=img_tk)  # Asignamos la nueva imagen al visor de video
        lbl_video.image = img_tk  # Conservamos la referencia para impedir que el recolector de basura la elimine
        lbl_telemetria.configure(text=f"Nudos Totales: {nudos}\nPasos: {pasos}")  # Actualizamos contadores en pantalla

    while ejecutando_vision:  # Bucle continuo mientras la aplicación permanezca abierta
        ret, frame = cap.read()  # Capturamos un nuevo fotograma desde la cámara USB
        if not ret:  # Verificamos si falló la lectura de la cámara
            break  # Salimos del bucle si no hay señal de video válida

        # 1. Leer parámetros en vivo de la interfaz HMI
        umbral_actual = var_umbral.get()  # Obtenemos el umbral oscuro configurado por el operario
        y1_actual = var_roi_y1.get()  # Obtenemos el recorte vertical superior actual
        y2_actual = var_roi_y2.get()  # Obtenemos el recorte vertical inferior actual

        # 2. Recortar ROI y convertir a escala de grises
        frame_roi = frame[y1_actual:y2_actual, ROI_X1:ROI_X2]  # Recortamos la matriz al rectángulo de inspección
        gris = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)  # Aplanamos de 3 canales BGR a 1 canal de luminancia
        brillo_promedio = cv2.mean(gris)[0]  # Calculamos el brillo medio para detectar si hay madera presente
        lista_cajas_crudas = []  # Inicializamos la lista de contornos detectados en este fotograma

        # 3. Evaluación de presencia de madera y pipeline de visión
        if brillo_promedio > UMBRAL_MADERA_PRESENTE:  # Si el brillo supera el umbral, hay un listón en la cinta
            if not madera_en_cinta:  # Si en el ciclo anterior la cinta estaba vacía, acaba de entrar una tabla nueva
                madera_en_cinta = True  # Marcamos presencia activa de madera
                com.enviar_comando_reset_odometria(arduino)  # Enviamos 'R\n' para poner a cero la odometría y la FIFO

            desenfoque = cv2.GaussianBlur(gris, (5, 5), 0)  # Aplicamos filtro Gaussiano para eliminar ruido y aserrín
            _, umbral = cv2.threshold(desenfoque, umbral_actual, 255, cv2.THRESH_BINARY_INV)  # Binarizamos zonas oscuras en blanco
            contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # Extraemos contornos externos

            for contorno in contornos:  # Recorremos cada mancha oscura detectada en el ROI
                area = cv2.contourArea(contorno)  # Calculamos el área en píxeles cuadrados del contorno
                if area > AREA_MINIMA:  # Filtramos manchas pequeñas que no corresponden a nudos estructurales
                    x, y, w, h = cv2.boundingRect(contorno)  # Obtenemos el rectángulo delimitador del defecto
                    lista_cajas_crudas.append((x, y, w, h))  # Agregamos la caja válida a la lista cruda

            # Agrupamos nudos cercanos a lo largo del eje horizontal X (requiere vision.py actualizado a X)
            cajas_procesadas = agrupar_defectos_cercanos(lista_cajas_crudas, DISTANCIA_MINIMA_PIXELES)  # Unificamos defectos próximos

            if len(cajas_procesadas) > 0:  # Si existe al menos un nudo consolidado dentro del ROI
                # Tomamos el último elemento [-1] porque vision.py ordena de izquierda a derecha: [-1] es el más cercano a X2
                x_fin, y_fin, w_fin, h_fin = cajas_procesadas[-1]  # Desempaquetamos las coordenadas del nudo delantero
                borde_izquierdo = x_fin  # Borde trasero del nudo (segundo punto que llegará a la sierra)
                borde_derecho = x_fin + w_fin  # Borde delantero del nudo (primer punto que llegará a la sierra)
                ancho_roi = ROI_X2 - ROI_X1  # Ancho útil total del ROI en píxeles

                # Definimos los límites horizontales del Gatillo Seguro para asegurar que el nudo se vea entero
                limite_seguridad_izquierdo = MARGEN_SEGURIDAD_PIXELES  # Margen mínimo desde la entrada X1
                limite_seguridad_derecho = ancho_roi - MARGEN_SEGURIDAD_PIXELES  # Margen mínimo antes de la salida X2

                # Lógica de desbloqueo al avanzar de izquierda (X1) a derecha (X2)
                if bloqueo_lectura_nudo:  # Si ya registramos el nudo que venía viajando
                    if borde_izquierdo < (ultimo_x_registrado - 40):  # Si X saltó hacia atrás, el nudo anterior ya salió por X2
                        bloqueo_lectura_nudo = False  # Liberamos el bloqueo para procesar el nuevo defecto
                    else:  # Si el mismo defecto continúa avanzando hacia la derecha
                        ultimo_x_registrado = borde_izquierdo  # Actualizamos el seguimiento de su coordenada X

                # Verificamos si el nudo está completamente contenido dentro del Gatillo Seguro
                if borde_derecho < limite_seguridad_derecho and borde_izquierdo > limite_seguridad_izquierdo:
                    if not bloqueo_lectura_nudo:  # Si todavía no fue enviado al Arduino
                        bloqueo_lectura_nudo = True  # Activamos el bloqueo para no duplicar la orden de corte
                        ultimo_x_registrado = borde_izquierdo  # Guardamos su posición X de disparo

                        # Calculamos Δpx (distancia restante en píxeles desde cada borde del nudo hasta la salida X2)
                        delta_px_1 = ancho_roi - borde_derecho  # Distancia restante del borde delantero hasta X2
                        delta_px_2 = ancho_roi - borde_izquierdo  # Distancia restante del borde trasero hasta X2

                        # Aplicamos la fórmula del Pre-proyecto sumando offset de 1000 mm y margen de seguridad por lado
                        dist_corte_1_mm = (delta_px_1 / PIXELES_POR_MM) + OFFSET_SIERRA_MM - MARGEN_SEGURIDAD_MM  # 1° corte
                        dist_corte_2_mm = (delta_px_2 / PIXELES_POR_MM) + OFFSET_SIERRA_MM + MARGEN_SEGURIDAD_MM  # 2° corte

                        # Convertimos ambos recorridos en milímetros a pulsos STEP relativos para el Arduino
                        pasos_corte_1 = int(dist_corte_1_mm * PASOS_POR_MM)  # Pasos hasta el corte frontal
                        pasos_corte_2 = int(dist_corte_2_mm * PASOS_POR_MM)  # Pasos hasta el corte trasero

                        com.enviar_comando_corte(arduino, pasos_corte_1, pasos_corte_2)  # Transmitimos trama Q:pasos1|pasos2\n
                        nudos_totales += 1  # Incrementamos el contador global de defectos procesados

                        # Dibujamos rectángulo verde indicando disparo confirmado en este fotograma
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (borde_derecho, y_fin + h_fin), (0, 255, 0), 3)
                    else:
                        # Dibujamos rectángulo rojo indicando defecto ya registrado y bloqueado
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (borde_derecho, y_fin + h_fin), (0, 0, 255), 3)
                else:
                    if bloqueo_lectura_nudo:  # Si el nudo ya registrado está abandonando la zona por el borde X2
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (borde_derecho, y_fin + h_fin), (0, 0, 255), 3)  # Marco rojo
                    else:  # Si el nudo recién entra por X1 y aún no entra completo al Gatillo Seguro
                        cv2.rectangle(frame_roi, (x_fin, y_fin), (borde_derecho, y_fin + h_fin), (0, 255, 255), 2)  # Marco amarillo
            else:
                bloqueo_lectura_nudo = False  # Si no hay defectos visibles en el ROI, aseguramos bloqueo liberado
                ultimo_x_registrado = 0  # Reiniciamos la referencia horizontal de seguimiento
        else:
            # No hay madera bajo la cámara: reseteamos estado para detectar la próxima tabla nueva
            madera_en_cinta = False  # Habilita el envío de 'R\n' cuando ingrese el siguiente listón
            bloqueo_lectura_nudo = False  # Liberamos cualquier bloqueo residual
            ultimo_x_registrado = 0  # Reiniciamos la última posición X registrada

        # 4. Comunicación serie continua (arranque y recepción de telemetría sin cortes)
        if estado_actual_motor != "AVANZANDO":  # Si aún no enviamos la orden de marcha continua
            com.enviar_comando_avance(arduino)  # Enviamos 'A\n' para habilitar el avance del motor
            estado_actual_motor = "AVANZANDO"  # Actualizamos el estado local para no reenviar en cada frame

        if arduino and arduino.in_waiting > 0:  # Verificamos si hay bytes entrantes desde Arduino
            try:
                datos = arduino.read(arduino.in_waiting).decode("utf-8", errors="ignore")  # Leemos todo lo disponible sin bloquear
                buffer_serial += datos  # Acumulamos en el buffer hasta completar al menos un salto de línea
                while "\n" in buffer_serial:  # Procesamos todas las líneas completas que hayan llegado
                    linea_serial, buffer_serial = buffer_serial.split("\n", 1)  # Separamos la primera línea completa
                    linea_serial = linea_serial.strip()  # Quitamos espacios y retorno de carro ('\r')
                    if linea_serial.startswith("ODOM:"):  # Verificamos si la trama corresponde a telemetría de pasos
                        odometria_actual = linea_serial.split(":", 1)[1]  # Extraemos el valor numérico del odómetro
            except Exception:  # Ignoramos errores puntuales de decodificación por ruido eléctrico
                pass

        # 5. Conversión a PIL y envío seguro al hilo principal de la HMI
        frame_rgb = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2RGB)  # Convertimos el espacio de color de BGR a RGB
        img_pil = Image.fromarray(frame_rgb)  # Creamos el objeto PIL en el hilo secundario (operación thread-safe)
        app.after(0, renderizar_gui, img_pil, nudos_totales, odometria_actual)  # Encolamos la actualización visual en el hilo principal

        time.sleep(0.01)  # Pausa breve de 10 ms para ceder tiempo de CPU al hilo gráfico y al sistema operativo

# ==========================================
# RUTINA DE CIERRE SEGURO
# ==========================================
def cerrar_app():  # Función ejecutada al cerrar la ventana principal
    global ejecutando_vision  # Accedemos a la bandera del bucle de visión
    ejecutando_vision = False  # Indicamos al hilo secundario que finalice su ejecución
    print("[!] Cerrando aplicación...")  # Informamos el cierre por consola
    hilo_vision.join(timeout=0.5)  # Esperamos brevemente a que el hilo libere la cámara antes de cerrarla
    cap.release()  # Liberamos el dispositivo de captura de video
    com.cerrar_conexion(arduino)  # Cerramos de forma segura el puerto serial del Arduino
    app.destroy()  # Destruimos la ventana gráfica y finalizamos el programa

app.protocol("WM_DELETE_WINDOW", cerrar_app)  # Asociamos el botón de cierre de la ventana a nuestra rutina segura

# Iniciamos el procesamiento de video en un hilo secundario tipo daemon
hilo_vision = threading.Thread(target=procesar_video, daemon=True)  # Creamos el hilo de visión
hilo_vision.start()  # Disparamos la ejecución en paralelo del hilo secundario

# Iniciamos el bucle de eventos de la ventana gráfica en el hilo principal
app.mainloop()  # Mantiene activa la interfaz HMI y procesa los eventos app.after()