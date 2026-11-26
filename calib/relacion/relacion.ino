// --- PINES DEL DRIVER ---
const int PIN_STEP = 4;
const int PIN_DIR = 5;

// --- CALIBRACIÓN MECÁNICA ---
// Constante teórica actual.
float pasosPorMilimetro = 3.4388; 

// --- CONSTANTES DE LA RAMPA ---
const int RETARDO_MAX_US = 2000;
const int RETARDO_MIN_US = 800;
const int PASOS_RAMPA = 400;

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH); // Sentido de avance
  
  Serial.println("=== TEST DE ODOMETRIA Y CALIBRACION ===");
  Serial.print("Constante actual: ");
  Serial.print(pasosPorMilimetro, 4);
  Serial.println(" pasos/mm");
  Serial.println("Ingresa la distancia en MILIMETROS que queres mover (ej: 100 o 500) y presiona Enter:");
  Serial.println("========================================\n");
}

void loop() {
  if (Serial.available() > 0) {
    // Leemos el valor ingresado hasta que se presione Enter
    float milimetrosObjetivo = Serial.parseFloat();
    
    // Limpiamos el buffer por si quedó un salto de línea
    while(Serial.available() > 0) Serial.read();

    if (milimetrosObjetivo > 0) {
      // 1. Conversión matemática
      long pasosCalculados = round(milimetrosObjetivo * pasosPorMilimetro);
      
      Serial.print("-> Orden recibida: ");
      Serial.print(milimetrosObjetivo);
      Serial.println(" mm.");
      Serial.print("-> Calculo: ");
      Serial.print(pasosCalculados);
      Serial.println(" pasos físicos.");
      Serial.println("-> Moviendo...");

      // 2. Ejecución física con rampa incluida
      ejecutarMovimientoConRampa(pasosCalculados);
      
      Serial.println("-> Movimiento finalizado. Medi la cinta y verifica.");
      Serial.println("Ingresa nueva distancia para otra prueba...\n");
    }
  }
}

// Función con la misma cinemática de tu código final
void ejecutarMovimientoConRampa(long pasosTotales) {
  long rampaEfectiva = PASOS_RAMPA;
  if (pasosTotales < (PASOS_RAMPA * 2)) {
    rampaEfectiva = pasosTotales / 2;
  }

  for (long i = 0; i < pasosTotales; i++) {
    long pasosRestantes = pasosTotales - i;
    int retardoActual = RETARDO_MIN_US;

    if (i < rampaEfectiva) {
      retardoActual = map(i, 0, rampaEfectiva, RETARDO_MAX_US, RETARDO_MIN_US);
    } 
    else if (pasosRestantes <= rampaEfectiva) {
      retardoActual = map(pasosRestantes, rampaEfectiva, 0, RETARDO_MIN_US, RETARDO_MAX_US);
    }

    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(retardoActual);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(retardoActual);
  }
}