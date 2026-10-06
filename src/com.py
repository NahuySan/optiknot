"""
Módulo para gestionar la comunicación serial con el controlador de hardware (Arduino).
Se encarga de establecer la conexión, enviar comandos y procesar las respuestas.
"""
import serial
import time

def inicializar_conexion(puerto, baudrate):
    """
    Intenta establecer la conexión serial con el controlador.
    Retorna el objeto serial si tiene éxito, o None si falla.
    """
    try:
        # Intentamos establecer comunicación con Arduino
        arduino = serial.Serial(puerto, baudrate, timeout=0)
        # Pausa obligatoria para que el microcontrolador reinicie y estabilice
        time.sleep(2)
        print("Comunicación serial establecida.")
        return arduino
    except Exception as e:
        # Si falla, imprimimos el error para diagnóstico
        print(f"Error de hardware: No se pudo abrir el puerto serie. Detalle: {e}")
        return None

def enviar_comando_corte(arduino, pasos_corte_1, pasos_corte_2):
    """
    Estructura y envía la trama de datos para ejecutar los cortes.
    Formato: Q:{pasos1}|{pasos2}\n
    """
    if arduino and arduino.is_open:
        # Estructuramos la cadena de caracteres (protocolo custom) para Arduino
        trama = f"Q:{pasos_corte_1}|{pasos_corte_2}\n"
        # Empujamos los comandos al buffer, pasándolo a bytes
        arduino.write(trama.encode())
        return True
    return False

def enviar_comando_avance(arduino):
    """
    Envía el comando para mantener el motor en régimen de avance continuo.
    Formato: A\n
    """
    if arduino and arduino.is_open:
        # Trama de comando "Avance continuo" hacia Arduino
        trama_serial = "A\n"
        # Enviamos el comando
        arduino.write(trama_serial.encode())
        return True
    return False

def cerrar_conexion(arduino):
    """Cierra de forma segura el puerto serial si está abierto."""
    if arduino and arduino.is_open:
        arduino.close()

def enviar_comando_reset_odometria(arduino):
    """
    Avisa al Arduino que ingresó una nueva tabla para resetear el cero absoluto.
    Formato: R\n
    """
    if arduino and arduino.is_open:
        arduino.write("R\n".encode())
        return True
    return False