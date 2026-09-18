// ==========================================
// DEFINICIÓN DE PINES FÍSICOS (ZONA LÓGICA 5V)
// ==========================================
// Pines cableados hacia los optoacopladores del driver R.T.A. X-PLUS B4.
const int PIN_STEP = 2; 
const int PIN_DIR = 3;  

// Pines de control para el módulo de relés de la neumática.
const int PIN_RELE_PISON = 4;
const int PIN_RELE_SIERRA = 5;
const int PIN_RELE_TRAMPILLA = 6;

// ==========================================
// CONSTANTES DE CALIBRACIÓN MECÁNICA Y TIEMPOS
// ==========================================
// Retardo en microsegundos que define la velocidad de giro del motor NEMA.
const int RETARDO_PULSO_US = "valor retardo_pulso_us";

// Factor de transmisión mecánica (cantidad de pulsos electrónicos para avanzar 1 milímetro).
const float PASOS_POR_MM = "valor pasos_por_mm"; 

// Tiempos de actuación neumática en milisegundos (ms).
const int TIEMPO_PISON_BAJA = "valor retardo_pison_baja";
const int TIEMPO_SIERRA_BAJA = "valor retardo_sierra_baja";
const int TIEMPO_SIERRA_SUBE = "valor retardo_sierra_sube";
const int TIEMPO_PISON_SUBE = "valor retardo_pison_sube";
const int TIEMPO_TRAMPILLA = "valor retardo_apertura_trampilla";

// ==========================================
// VARIABLES DE ESTADO GLOBALES
// ==========================================
// Buffer temporal para la orden recibida por USB.
String tramaSerial = "";
// Bandera lógica que habilita o interrumpe la tracción continua.
bool modoAvance = false;

// ==========================================
// RUTINA DE INICIALIZACIÓN (SETUP)
// ==========================================
void setup() {
  // Inicialización del puerto serie para recibir los comandos de Python.
  Serial.begin(9600);
  
  // Configuración de los pines de odometría.
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  
  // Configuración de los pines de disparo de los relés.
  pinMode(PIN_RELE_PISON, OUTPUT);
  pinMode(PIN_RELE_SIERRA, OUTPUT);
  pinMode(PIN_RELE_TRAMPILLA, OUTPUT);
  
  // Estado inicial del motor: frenado y configurado hacia adelante.
  digitalWrite(PIN_STEP, LOW);
  digitalWrite(PIN_DIR, HIGH); 
  
  // Estado inicial de la neumática (Lógica Inversa: HIGH = Relé apagado / Válvula cerrada).
  digitalWrite(PIN_RELE_PISON, HIGH);
  digitalWrite(PIN_RELE_SIERRA, HIGH);
  digitalWrite(PIN_RELE_TRAMPILLA, HIGH);
}

// ==========================================
// BUCLE PRINCIPAL (MÁQUINA DE ESTADOS)
// ==========================================
void loop() {
  
  // 1. ESCUCHA Y PARSEO DE INSTRUCCIONES SERIALES
  if (Serial.available() > 0) {
    // Lectura de la trama completa hasta el salto de línea.
    tramaSerial = Serial.readStringUntil('\n');
    
    if (tramaSerial == "A") {
      // Orden de avance continuo. Madera sin nudos críticos.
      modoAvance = true;
    } 
    else if (tramaSerial.startsWith("C:")) {
      // Orden de corte. Se aborta la tracción.
      modoAvance = false;
      
      // Extracción del valor numérico de la trama entrante.
      String valorDistanciaStr = tramaSerial.substring(2);
      float distanciaMm = valorDistanciaStr.toFloat();
      
      // Llamada a la función bloqueante de actuación mecánica.
      rutinaCorteNeumatico(distanciaMm);
      
      // Finalizada la actuación, se rehabilita la tracción para la siguiente iteración.
      modoAvance = true;
    }
  }

  // 2. EJECUCIÓN DE TRACCIÓN (PULSOS AL DRIVER)
  if (modoAvance) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
}

// ==========================================
// RUTINAS DE EJECUCIÓN FÍSICA
// ==========================================
void rutinaCorteNeumatico(float distanciaObjetivoMm) {
  // Conversión de distancia física a micropasos del motor.
  long pasosRequeridos = (long)(distanciaObjetivoMm * PASOS_POR_MM);
  
  // Fase 1: Posicionamiento milimétrico del defecto bajo la sierra.
  for (long i = 0; i < pasosRequeridos; i++) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
  
  // Fase 2: Secuencia de amputación neumática.
  // Se acciona el pisón para fijar la tabla.
  digitalWrite(PIN_RELE_PISON, LOW);
  delay(TIEMPO_PISON_BAJA); 
  
  // Se acciona el descenso transversal de la sierra.
  digitalWrite(PIN_RELE_SIERRA, LOW);
  delay(TIEMPO_SIERRA_BAJA); 
  
  // Se retrae la sierra a la posición segura superior.
  digitalWrite(PIN_RELE_SIERRA, HIGH);
  delay(TIEMPO_SIERRA_SUBE); 
  
  // Se libera la presión del pisón sobre la tabla.
  digitalWrite(PIN_RELE_PISON, HIGH);
  delay(TIEMPO_PISON_SUBE);
  
  // Se abre la trampilla inferior para el descarte del nudo.
  digitalWrite(PIN_RELE_TRAMPILLA, LOW);
  delay(TIEMPO_TRAMPILLA); 
  digitalWrite(PIN_RELE_TRAMPILLA, HIGH);
  
  // La rutina finaliza y devuelve el control al bucle principal.
}