from pyModbusTCP.server import ModbusServer, DataBank

# Instanciamos el servidor en el puerto 5020 (no bloqueante)
server = ModbusServer("127.0.0.1", 5020, no_block=True)

def iniciar():
    try:
        server.start()
        # Valores por defecto al arrancar: ROI X, ROI Y, Ancho, Alto, Umbral
        DataBank.set_words(10, [20, 65, 600, 350, 80])
        print("[+] Servidor SCADA iniciado en 127.0.0.1:5020")
    except Exception as e:
        print(f"[!] Error al iniciar Modbus: {e}")

def leer_variables_camara():
    """Lee los registros de Ignition y los devuelve formateados"""
    valores = DataBank.get_words(10, 5)
    if valores:
        return valores[0], valores[1], valores[2], valores[3], valores[4]
    else:
        # Fallback de seguridad si falla la red
        return 20, 65, 600, 350, 80 

def actualizar_telemetria(nudos_totales):
    """Escribe datos hacia Ignition (ej. en el registro 0)"""
    DataBank.set_words(0, [nudos_totales])