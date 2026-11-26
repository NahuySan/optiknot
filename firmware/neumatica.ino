// ==========================================
// FUNCIONES DE SIMULACIÓN DE CORTE (LÁSER)
// ==========================================

// Tiempos para el prototipo visual (en milisegundos)
const int TIEMPO_LASER = 1000;       // Tiempo que el láser se mantiene encendido sobre la marca
const int TIEMPO_PAUSA_MOTOR = 200;  // Pequeña pausa antes de reanudar la marcha para evitar tirones

// Esta es la función que gatilla el corte desde ejecutarOdometriaYCortes()
void iniciarCorte() {
  if (!corteEnProceso) {
    corteEnProceso = true;
    estadoCorte = 1; // Dispara la fase 1 de la máquina de estados del láser
  }
}

// Se ejecuta constantemente en el loop() sin bloquear el código
void gestionarCorteEstado() {
  if (!corteEnProceso) return; 

  unsigned long tiempoActual = millis();

  switch (estadoCorte) {
    
    case 1: // FASE 1: Detener avance visual y encender láser
      // digitalWrite(PIN_LED_MOTOR, LOW); // (Descomentar si usás el LED testigo)
      
      // Encendemos el láser (Recordá que el relé simple usa HIGH para encender)
      digitalWrite(PIN_LASER, HIGH); 
      
      timerCorte = tiempoActual;         
      estadoCorte = 2;                   
      break;

    case 2: // FASE 2: Mantener encendido y luego apagar
      // Solo avanza cuando pasó el tiempo visual programado
      if (tiempoActual - timerCorte >= TIEMPO_LASER) {
        
        digitalWrite(PIN_LASER, LOW); // Apagamos el láser
        
        timerCorte = tiempoActual;
        estadoCorte = 3;
      }
      break;

    case 3: // FASE 3: Pausa de seguridad y reinicio de marcha
      if (tiempoActual - timerCorte >= TIEMPO_PAUSA_MOTOR) {
        // digitalWrite(PIN_LED_MOTOR, HIGH); 
        
        corteEnProceso = false;              // Liberamos la bandera
        estadoCorte = 0;                     // Reseteamos la máquina de estados
        
        modoAvance = true;                   // Arranca el motor nuevamente
      }
      break;
  }
}

// ==============================================================================
// RESPALDO DE LÓGICA NEUMÁTICA PARA EL FUTURO (NO BORRAR)
// ==============================================================================
/*
void gestionarCorteEstadoNeumatico() {
  if (!corteEnProceso) return;

  unsigned long tiempoActual = millis();

  switch (estadoCorte) {

    case 1: // FASE 1: Motor detenido y bajar pisón
      // digitalWrite(PIN_LED_MOTOR, LOW);
      digitalWrite(PIN_RELE_PISON, LOW); // Lógica negada
      timerCorte = tiempoActual;
      estadoCorte = 2;
      break;

    case 2: // FASE 2: Esperar pisón abajo y subir sierra (sierra inferior)
      if (tiempoActual - timerCorte >= TIEMPO_PISON_BAJA) {
        digitalWrite(PIN_RELE_SIERRA, LOW);
        timerCorte = tiempoActual;
        estadoCorte = 3;
      }
      break;

    case 3: // FASE 3: Esperar corte (sierra arriba) y bajar sierra
      if (tiempoActual - timerCorte >= TIEMPO_SIERRA_SUBE) {
        digitalWrite(PIN_RELE_SIERRA, HIGH);
        timerCorte = tiempoActual;
        estadoCorte = 4;
      }
      break;

    case 4: // FASE 4: Esperar sierra abajo (reposo) y subir pisón
      if (tiempoActual - timerCorte >= TIEMPO_SIERRA_BAJA) {
        digitalWrite(PIN_RELE_PISON, HIGH);
        timerCorte = tiempoActual;
        estadoCorte = 5;
      }
      break;

    case 5: // FASE 5: Esperar pisón arriba y reanudar avance
      if (tiempoActual - timerCorte >= TIEMPO_PISON_SUBE) {
        // digitalWrite(PIN_LED_MOTOR, HIGH);
        corteEnProceso = false;
        estadoCorte = 0;
        modoAvance = true;
      }
      break;
  }
}
*/