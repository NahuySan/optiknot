

// ==========================================
// FUNCIONES DE NEUMÁTICA
// ==========================================

// Esta es la función que vas a llamar una sola vez para "gatillar" el corte
// desde la función ejecutarOdometriaYCortes() cuando coincidan los pasos.
void iniciarCorte() {
  if (!corteEnProceso) {
    corteEnProceso = true;
    estadoCorte = 1; // Dispara la fase 1 de la máquina de estados
  }
}

// Esta función debe ir adentro del loop() principal para que se ejecute constantemente.
// Entra, revisa si hay que hacer algo, lo hace, y sale al instante.
void gestionarCorteEstado() {
  // Si no hay ningún corte activo, salimos de la función sin perder tiempo
  if (!corteEnProceso) return; 

  unsigned long tiempoActual = millis();

  // Máquina de estados: evalúa en qué fase de la secuencia neumática estamos
  switch (estadoCorte) {
    
    case 1: // FASE 1: Apagar motor y bajar pisón
      digitalWrite(PIN_LED_MOTOR, LOW);
      digitalWrite(PIN_RELE_PISON, LOW); // Lógica negada: activa el cilindro del pisón
      
      timerCorte = tiempoActual;         // Guardamos el momento exacto en que bajó
      estadoCorte = 2;                   // Pasamos a esperar en la siguiente fase
      break;

    case 2: // FASE 2: Esperar que baje el pisón y luego bajar sierra
      // Solo entra si ya transcurrió el TIEMPO_PISON_BAJA
      if (tiempoActual - timerCorte >= TIEMPO_PISON_BAJA) {
        digitalWrite(PIN_RELE_SIERRA, LOW); // Activa cilindro de la sierra
        
        timerCorte = tiempoActual;
        estadoCorte = 3;
      }
      break;

    case 3: // FASE 3: Esperar que baje la sierra y luego subir sierra
      if (tiempoActual - timerCorte >= TIEMPO_SIERRA_BAJA) {
        digitalWrite(PIN_RELE_SIERRA, HIGH); // Desactiva sierra (la sube)
        
        timerCorte = tiempoActual;
        estadoCorte = 4;
      }
      break;

    case 4: // FASE 4: Esperar que suba la sierra y luego subir pisón
      if (tiempoActual - timerCorte >= TIEMPO_SIERRA_SUBE) {
        digitalWrite(PIN_RELE_PISON, HIGH);  // Desactiva pisón (libera la madera)
        
        timerCorte = tiempoActual;
        estadoCorte = 5;
      }
      break;

    case 5: // FASE 5: Esperar que suba el pisón y finalizar
      if (tiempoActual - timerCorte >= TIEMPO_PISON_SUBE) {
        digitalWrite(PIN_LED_MOTOR, HIGH);   // Indicador de avance listo
        
        corteEnProceso = false;              // Liberamos la bandera
        estadoCorte = 0;                     // Reseteamos la máquina de estados
        
        modoAvance = true;                   //Arranca el motor

      }
      break;
  }
}

// La función original la dejamos intacta.
/*void controlTrampilla() {
  if (trampillaAbierta && millis() >= timerTrampilla) {
    digitalWrite(PIN_RELE_TRAMPILLA, HIGH);
    trampillaAbierta = false;
  }
}*/