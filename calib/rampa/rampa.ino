// --- PINES DEL DRIVER ---
const int PIN_STEP = 4;
const int PIN_DIR = 5;

// --- CONSTANTES DE LA RAMPA ---
const int RETARDO_MAX_US = 2000;  // Arranque lento
const int RETARDO_MIN_US = 800;   // Velocidad crucero
const int PASOS_RAMPA = 400;      // Longitud estándar de la rampa

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH); // Sentido de avance fijo
  
  Serial.println("=== TEST DE RAMPAS DE ACELERACION ===");
  Serial.println("Envia un numero por el monitor serie:");
  Serial.println("1 -> Rampa Trapezoidal Larga (2000 pasos / ~580 mm)");
  Serial.println("2 -> Rampa Trapezoidal Justa (800 pasos / ~232 mm)");
  Serial.println("3 -> Rampa Triangular Corta  (300 pasos / ~87 mm)");
  Serial.println("4 -> Rampa Triangular Micro  (100 pasos / ~29 mm)");
  Serial.println("=====================================\n");
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    // Ignorar saltos de línea
    if (comando == '\n' || comando == '\r') return;

    switch (comando) {
      case '1':
        Serial.println("Ejecutando Trapezoidal Larga (2000 pasos)...");
        ejecutarMovimiento(2000);
        break;
      case '2':
        Serial.println("Ejecutando Trapezoidal Justa (800 pasos)...");
        ejecutarMovimiento(800);
        break;
      case '3':
        Serial.println("Ejecutando Triangular Corta (300 pasos)...");
        ejecutarMovimiento(300);
        break;
      case '4':
        Serial.println("Ejecutando Triangular Micro (100 pasos)...");
        ejecutarMovimiento(100);
        break;
      default:
        Serial.println("Comando invalido. Envia 1, 2, 3 o 4.");
        break;
    }
  }
}

// Función aislada que recrea la matemática del código de producción
void ejecutarMovimiento(long pasosTotales) {
  
  // 1. Definir longitud efectiva de la rampa
  long rampaEfectiva = PASOS_RAMPA;
  if (pasosTotales < (PASOS_RAMPA * 2)) {
    rampaEfectiva = pasosTotales / 2; // Activa el perfil triangular
  }

  // Desplegamos datos por consola antes de mover para no arruinar los microsegundos
  Serial.print(" -> Rampa efectiva seteada en: ");
  Serial.print(rampaEfectiva);
  Serial.println(" pasos por extremo.");

  // 2. Bucle de movimiento
  for (long i = 0; i < pasosTotales; i++) {
    long pasosRestantes = pasosTotales - i;
    int retardoActual = RETARDO_MIN_US;

    // Fase de aceleración
    if (i < rampaEfectiva) {
      retardoActual = map(i, 0, rampaEfectiva, RETARDO_MAX_US, RETARDO_MIN_US);
    } 
    // Fase de desaceleración
    else if (pasosRestantes <= rampaEfectiva) {
      retardoActual = map(pasosRestantes, rampaEfectiva, 0, RETARDO_MIN_US, RETARDO_MAX_US);
    }
    // (Si no entra en ningún 'if', usa el RETARDO_MIN_US de la velocidad crucero)

    // 3. Emisión del pulso 
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(retardoActual);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(retardoActual);
  }
  
  Serial.println("Movimiento finalizado.\n");
}