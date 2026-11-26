// --- PINES DEL DRIVER ---
const int PIN_STEP = 4;
const int PIN_DIR = 5;

// --- CONSTANTES DE LA RAMPA ---
const int RETARDO_MAX_US = 2000;
const int RETARDO_MIN_US = 800;
const int PASOS_RAMPA = 400;

// --- VARIABLES DE ESTADO ---
// 0: Parado | 1: Acelerando | 2: Crucero infinito | 3: Frenando
int estadoMotor = 0; 
long pasosRampa = 0;

void setup() {
  Serial.begin(115200);
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH); // Sentido de avance
  
  Serial.println("=== MODO MARCHA CONTINUA ===");
  Serial.println("'I' -> Iniciar marcha (acelera y queda en crucero)");
  Serial.println("'P' -> Parar (desacelera y se detiene)");
  Serial.println("=============================\n");
}

void loop() {
  // 1. Escuchar comandos sin bloquear el motor
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    // Ignorar saltos de línea del monitor serie
    if (comando == '\n' || comando == '\r') return;
    
    if ((comando == 'I' || comando == 'i') && estadoMotor == 0) {
      estadoMotor = 1;
      pasosRampa = 0;
      Serial.println("-> Acelerando...");
    } 
    else if ((comando == 'P' || comando == 'p') && (estadoMotor == 1 || estadoMotor == 2)) {
      // Si venía en crucero, la rampa de frenado arranca limpia desde 0
      if (estadoMotor == 2) {
        pasosRampa = 0;
      } 
      // Si le diste 'P' justo cuando estaba acelerando, invertimos el contador
      // para que frene suave desde la velocidad a la que haya llegado.
      else {
        pasosRampa = PASOS_RAMPA - pasosRampa; 
      }
      
      estadoMotor = 3;
      Serial.println("-> Frenando...");
    }
  }

  // 2. Ejecutar el pulso físico según el estado actual
  if (estadoMotor != 0) {
    int retardoActual = RETARDO_MIN_US; // Por defecto usa la velocidad máxima (Crucero)

    if (estadoMotor == 1) { // Fase de Aceleración
      retardoActual = map(pasosRampa, 0, PASOS_RAMPA, RETARDO_MAX_US, RETARDO_MIN_US);
      pasosRampa++;
      if (pasosRampa >= PASOS_RAMPA) {
        estadoMotor = 2; // Termina la rampa y pasa a crucero infinito
        Serial.println("-> Velocidad crucero alcanzada. Viajando...");
      }
    } 
    else if (estadoMotor == 3) { // Fase de Desaceleración
      retardoActual = map(pasosRampa, 0, PASOS_RAMPA, RETARDO_MIN_US, RETARDO_MAX_US);
      pasosRampa++;
      if (pasosRampa >= PASOS_RAMPA) {
        estadoMotor = 0; // Termina de frenar y se clava
        Serial.println("-> Motor detenido en seco.");
      }
    }

    // Inyectar el pulso al driver RTA
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(retardoActual);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(retardoActual);
  }
}