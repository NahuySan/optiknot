// ==========================================
// DEFINICIÓN DE PINES FÍSICOS (ZONA LÓGICA 5V)
// ==========================================
const int PIN_STEP = 4; 
const int PIN_DIR = 5;  
const int PIN_RELE_PISON = 6;     
const int PIN_RELE_SIERRA = 7;    
const int PIN_RELE_TRAMPILLA = 8; 
const int PIN_LED_MOTOR = 9;

// ==========================================
// CONSTANTES DE CALIBRACIÓN MECÁNICA Y TIEMPOS
// ==========================================
const int RETARDO_PULSO_US = 800;
const float PASOS_POR_MM = 10.0; 

const int TIEMPO_PISON_BAJA = 1000;   
const int TIEMPO_SIERRA_BAJA = 1000;  
const int TIEMPO_SIERRA_SUBE = 1000;  
const int TIEMPO_PISON_SUBE = 1000;   
const int TIEMPO_TRAMPILLA = 1500;    

// ==========================================
// VARIABLES GLOBALES
// ==========================================
String tramaSerial = "";
bool modoAvance = false;

// Variables para el control asíncrono de la trampilla
unsigned long timerTrampilla = 0;
bool trampillaAbierta = false;

void setup() {
  Serial.begin(9600);
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_LED_MOTOR, OUTPUT);
  pinMode(PIN_RELE_PISON, OUTPUT);
  pinMode(PIN_RELE_SIERRA, OUTPUT);
  pinMode(PIN_RELE_TRAMPILLA, OUTPUT);
  
  digitalWrite(PIN_STEP, LOW);
  digitalWrite(PIN_DIR, HIGH); 
  
  digitalWrite(PIN_RELE_PISON, HIGH);
  digitalWrite(PIN_RELE_SIERRA, HIGH);
  digitalWrite(PIN_RELE_TRAMPILLA, HIGH);
  digitalWrite(PIN_LED_MOTOR, LOW);
}

void loop() {
  
  // 1. CONTROL ASÍNCRONO DE LA TRAMPILLA
  // Permite cerrar la trampilla sin bloquear el avance del motor
  if (trampillaAbierta && millis() >= timerTrampilla) {
    digitalWrite(PIN_RELE_TRAMPILLA, HIGH); // Apaga relé (Lógica inversa)
    trampillaAbierta = false;
  }

  // 2. ESCUCHA Y PARSEO DE INSTRUCCIONES
  if (Serial.available() > 0) {
    tramaSerial = Serial.readStringUntil('\n');
    tramaSerial.trim();
    
    if (tramaSerial == "A") {
      modoAvance = true;
      digitalWrite(PIN_LED_MOTOR, HIGH);
    } 
    else if (tramaSerial.startsWith("C:")) {
      modoAvance = false;
      
      // Parseo del comando estructurado "C:DistanciaInicio|DistanciaNudo"
      int separador = tramaSerial.indexOf('|');
      float distOffset = tramaSerial.substring(2, separador).toFloat();
      float distNudo = tramaSerial.substring(separador + 1).toFloat();
      
      // Ejecución de la rutina completa
      rutinaAmputacionCompleta(distOffset, distNudo);
      
      // Se reanuda la marcha al finalizar los cortes
      modoAvance = true;
      digitalWrite(PIN_LED_MOTOR, HIGH);
    }
  }

  // 3. EJECUCIÓN DE TRACCIÓN PRINCIPAL
  if (modoAvance) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
}

// ==========================================
// RUTINA DE EJECUCIÓN FÍSICA UNIFICADA
// ==========================================
void rutinaAmputacionCompleta(float distOffset, float distNudo) {
  long pasosOffset = (long)(distOffset * PASOS_POR_MM);
  long pasosNudo = (long)(distNudo * PASOS_POR_MM);
  
  // FASE 1: Avance al punto del primer corte
  digitalWrite(PIN_LED_MOTOR, HIGH); // Motor "avanzando"
  for (long i = 0; i < pasosOffset; i++) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
  
  // FASE 2: Primer Corte (Frontal)
  digitalWrite(PIN_LED_MOTOR, LOW); // Motor detenido
  digitalWrite(PIN_RELE_PISON, LOW); delay(TIEMPO_PISON_BAJA); 
  digitalWrite(PIN_RELE_SIERRA, LOW); delay(TIEMPO_SIERRA_BAJA); 
  digitalWrite(PIN_RELE_SIERRA, HIGH); delay(TIEMPO_SIERRA_SUBE); 
  digitalWrite(PIN_RELE_PISON, HIGH); delay(TIEMPO_PISON_SUBE);
  
  // FASE 3: Avance para encapsular el nudo
  digitalWrite(PIN_LED_MOTOR, HIGH); // Motor "avanzando"
  for (long i = 0; i < pasosNudo; i++) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
  }
  
  // FASE 4: Segundo Corte (Trasero)
  digitalWrite(PIN_LED_MOTOR, LOW); // Motor detenido
  digitalWrite(PIN_RELE_PISON, LOW); delay(TIEMPO_PISON_BAJA); 
  digitalWrite(PIN_RELE_SIERRA, LOW); delay(TIEMPO_SIERRA_BAJA); 
  digitalWrite(PIN_RELE_SIERRA, HIGH); delay(TIEMPO_SIERRA_SUBE); 
  digitalWrite(PIN_RELE_PISON, HIGH); delay(TIEMPO_PISON_SUBE);
  
  // FASE 5: Apertura de trampilla asíncrona
  digitalWrite(PIN_RELE_TRAMPILLA, LOW);
  trampillaAbierta = true;
  timerTrampilla = millis() + TIEMPO_TRAMPILLA;
  // Al salir de la función, el loop principal toma el control, tracciona y la cierra cuando expira el timer.
}

//mi idea es esta para hacer prubeas: hacer que la camara reconozca el nudo, python avisa que reconocio al nudo y que baje la cierra despues de x pasos (que va a ser la distancia a la que esta la sierra del punto de reconocimineto de la camara) para el primer corte y para el segundo que calcule el tamaño del nudo reconocido y haga el corte basandose en el calculo que hizo del nudo, vamos a poner para las pruebas, la tabla a 50cm de la camara.