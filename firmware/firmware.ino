// ==========================================
// DEFINICIÓN DE PINES FÍSICOS (ZONA LÓGICA 5V)
// ==========================================
const int PIN_STEP = 4;
const int PIN_DIR = 5;
//const int PIN_RELE_PISON = 6;
const int PIN_LASER = 7;
//const int PIN_RELE_TRAMPILLA = 8;
//const int PIN_LED_MOTOR = 9;

// ==========================================
// CONSTANTES DE CALIBRACIÓN MECÁNICA Y TIEMPOS
// ==========================================
const int RETARDO_PULSO_US = 800;
//const int TIEMPO_PISON_BAJA = 2000;
//const int TIEMPO_SIERRA_BAJA = 2000;
//const int TIEMPO_SIERRA_SUBE = 2000;
//const int TIEMPO_PISON_SUBE = 2000;
//const int TIEMPO_TRAMPILLA = 2000;

// ==========================================
// VARIABLES GLOBALES DE ESTADO
// ==========================================
String tramaSerial = "";
bool modoAvance = false;
long posicionAbsolutaCinta = 0;
//unsigned long timerTrampilla = 0;
//bool trampillaAbierta = false;
unsigned long timerTelemetria = 0;

//===========================================
// VARIABLES PARA LA MAQUINA DE ESTADOS DE CORTE
//===========================================
int estadoCorte = 0;              
unsigned long timerCorte = 0;     
bool corteEnProceso = false;

// ==========================================
// ESTRUCTURA DE DATOS: COLA DE TAREAS (FIFO)
// ==========================================
struct TareaEncapsulado {
  long pasoCorteFrontal;
  long pasoCorteTrasero;
  bool primerCorteHecho;
};

const int MAX_TAREAS = 10;
TareaEncapsulado colaTareas[MAX_TAREAS];
int indiceLectura = 0;
int indiceEscritura = 0;
int cantidadTareas = 0;

void setup() {
  Serial.begin(115200); // Velocidad industrial para no perder tramas de visión
  tramaSerial.reserve(50); // Previene que el Arduino se cuelgue por falta de RAM
  
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  //pinMode(PIN_LED_MOTOR, OUTPUT);
  //pinMode(PIN_RELE_PISON, OUTPUT);
  pinMode(PIN_LASER, OUTPUT);
  //pinMode(PIN_RELE_TRAMPILLA, OUTPUT);
  
  digitalWrite(PIN_STEP, LOW);
  digitalWrite(PIN_DIR, HIGH); 
  
  // Mantiene los relés apagados al encender (asumiendo módulo activo en LOW)
  //digitalWrite(PIN_RELE_PISON, HIGH);
  digitalWrite(PIN_LASER, LOW);
  //digitalWrite(PIN_RELE_TRAMPILLA, HIGH);
  //digitalWrite(PIN_LED_MOTOR, LOW);
}

void loop() {
  //Funciones de los otros módulos
  //controlTrampilla();
  leerSerial();
  gestionarCorteEstado();
  ejecutarOdometriaYCortes();
  avanzarMotor();
  enviarTelemetria();
}