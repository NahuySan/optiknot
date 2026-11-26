// --- SCRIPT DE CALIBRACIÓN: RETORNO A CERO ---

// Definición de pines
const int PIN_STEP = 4;
const int PIN_DIR = 5;

// Parámetros mecánicos actuales a evaluar
const float PASOS_POR_MM = 3.4388;
const float DISTANCIA_PRUEBA_MM = 2000.0;
const int RETARDO_PULSO_US = 800;
const int RETARDO_MAX_US = 2000;
const int PASOS_RAMPA = 400;

// Cálculo de pasos
long pasosTotales = DISTANCIA_PRUEBA_MM * PASOS_POR_MM;

void setup() {
  Serial.begin(9600);
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_STEP, LOW);
  
  Serial.println("=== PRUEBA DE RETORNO A CERO ===");
  Serial.println("1. Hace una marca fina en la correa y otra alineada en el chasis.");
  Serial.print("2. Escribi 'T' y presiona Enter para avanzar y retroceder ");
  Serial.print(DISTANCIA_PRUEBA_MM);
  Serial.println(" mm.");
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    // Ignorar saltos de línea
    if (comando == '\n' || comando == '\r') return;
    
    if (comando == 'T' || comando == 't') {
      Serial.print("-> Avanzando ");
      Serial.print(pasosTotales);
      Serial.println(" pasos...");
      
      // Activar dirección de avance
      digitalWrite(PIN_DIR, HIGH); 
      darPasos(pasosTotales);
      
      Serial.println("-> Pausa de 2 segundos...");
      delay(2000);
      
      Serial.println("<- Retrocediendo al origen...");
      // Invertir dirección
      digitalWrite(PIN_DIR, LOW); 
      darPasos(pasosTotales);
      
      Serial.println("=== FIN DE PRUEBA ===");
      Serial.println("Revisa si las marcas coinciden EXACTAMENTE.");
      Serial.println("Escribi 'T' para repetir la prueba.\n");
    }
  }
}

// Función bloqueante simple para generar los pulsos

/*void darPasos(long cantidadPasos) {
  for (long i = 0; i < cantidadPasos; i++) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
}*/

void darPasos(long cantidadPasos) {
  // Ajuste por si el movimiento total es muy corto para completar dos rampas
  long rampaEfectiva = PASOS_RAMPA;
  if (cantidadPasos < (PASOS_RAMPA * 2)) {
    rampaEfectiva = cantidadPasos / 2;
  }

  int retardoActual = RETARDO_MAX_US;

  for (long i = 0; i < cantidadPasos; i++) {
    // 1. Tramo de aceleración
    if (i < rampaEfectiva) {
      retardoActual = map(i, 0, rampaEfectiva, RETARDO_MAX_US, RETARDO_PULSO_US);
    } 
    // 2. Tramo de desaceleración
    else if (i >= (cantidadPasos - rampaEfectiva)) {
      retardoActual = map(i, cantidadPasos - rampaEfectiva, cantidadPasos, RETARDO_PULSO_US, RETARDO_MAX_US);
    } 
    // 3. Velocidad crucero constante
    else {
      retardoActual = RETARDO_PULSO_US;
    }

    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(retardoActual);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(retardoActual);
  }
}
