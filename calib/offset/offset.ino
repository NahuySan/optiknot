// --- SCRIPT DE CALIBRACIÓN: OFFSET DE SIERRA CON LÁSER ENCENDIDO ---

const int PIN_STEP = 4;
const int PIN_DIR = 5;
const int PIN_LASER = 7; // Sierra neumática

// Usamos un retardo alto (1500) para que se mueva suave y se pueda medir precisamente
const int RETARDO_PULSO_US = 1500; 

long posicionActual = 0; 

void setup() {
  Serial.begin(115200);
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_LASER, OUTPUT);
  
  digitalWrite(PIN_STEP, LOW);
  
  // Encendemos el láser desde el primer momento para tener la referencia visual.
  // IMPORTANTE: Chequear lógica del relé
  digitalWrite(PIN_LASER, HIGH); 

  Serial.println("=== CALIBRACION DE SEPARACIÓN DE LA SIERRA DEL PUNTO 0 ===");
  Serial.println("1. Ubica la linea de la madera en el borde de salida (ROI) de la camara.");
  Serial.println("2. Envia 'R' para poner el contador en CERO.");
  Serial.println("3. Usa estos comandos y presiona Enter para mover la cinta:");
  Serial.println("   'F' -> Avanzar RAPIDO (1000 pasos)");
  Serial.println("   'M' -> Avanzar MEDIO (100 pasos)");
  Serial.println("   'L' -> Avanzar LENTO (10 pasos) - Para ajuste fino");
  Serial.println("   'B' -> Retroceder LENTO (10 pasos) - Por si te pasaste del laser");
  Serial.println("=======================================\n");
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    // Ignorar saltos de linea invisibles del monitor serie
    if (comando == '\n' || comando == '\r') return;

    // Convertir a mayúsculaS
    comando = toupper(comando);

    if (comando == 'R') {
      posicionActual = 0;
      Serial.println("-> Posicion RESETEADA. ¡Punto Cero fijado en la camara!");
    } 
    else if (comando == 'F') {
      Serial.print("Avanzando rapido... ");
      moverMotor(1000, HIGH);
    }
    else if (comando == 'M') {
      Serial.print("Avanzando medio... ");
      moverMotor(100, HIGH);
    }
    else if (comando == 'L') {
      Serial.print("Ajuste fino adelante... ");
      moverMotor(10, HIGH);
    }
    else if (comando == 'B') {
      Serial.print("Ajuste fino atras... ");
      moverMotor(10, LOW);
    }
    else {
      Serial.println("Comando no reconocido.");
    }
  }
}

// Función que mueve el motor y actualiza la odometría
void moverMotor(int pasos, int direccion) {
  digitalWrite(PIN_DIR, direccion);

  for (int i = 0; i < pasos; i++) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);

    // Actualizamos el odómetro interno sumando o restando según el sentido
    if (direccion == HIGH) {
      posicionActual++;
    } else {
      posicionActual--;
    }
  }

  // Escupe la posición final al terminar el movimiento
  Serial.print("Posicion odometro: ");
  Serial.print(posicionActual);
  Serial.println(" pasos.");
}