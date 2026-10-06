void enviarTelemetria() {
  // Cada 500 milisegundos escupe la posición actual al puerto COM
  if (millis() - timerTelemetria >= 500) {
    Serial.print("ODOM:");
    Serial.println(posicionAbsolutaCinta);
    timerTelemetria = millis();
  }
}

void avanzarMotor() {
  // Si la máquina no está avanzando (ej: está cortando), esta función no hace nada
  if (modoAvance) {
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(RETARDO_PULSO_US);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(RETARDO_PULSO_US);
    
    posicionAbsolutaCinta++;
  }
}

void ejecutarOdometriaYCortes() {
  // BLOQUEO DE SEGURIDAD: Si la neumática está actuando, no evaluamos cortes nuevos.
  // Esto evita que la lógica se vuelva a gatillar repetidas veces.
  if (corteEnProceso) return; 

  if (cantidadTareas > 0) {
    TareaEncapsulado &tareaActual = colaTareas[indiceLectura];
    
    // CORTE FRONTAL
    if (!tareaActual.primerCorteHecho && posicionAbsolutaCinta >= tareaActual.pasoCorteFrontal) {
      modoAvance = false;               // 1. FRENAMOS LA CINTA
      iniciarCorte();                   // 2. DISPARAMOS LA MÁQUINA DE ESTADOS
      tareaActual.primerCorteHecho = true;
    }
    // CORTE TRASERO Y DESCARTE
    else if (tareaActual.primerCorteHecho && posicionAbsolutaCinta >= tareaActual.pasoCorteTrasero) {
      modoAvance = false;               // 1. FRENAMOS LA CINTA
      iniciarCorte();                   // 2. DISPARAMOS LA MÁQUINA DE ESTADOS
      
      // Abrimos la trampilla de descarte (asumiendo lógica negada)
      //digitalWrite(PIN_RELE_TRAMPILLA, LOW);
      //trampillaAbierta = true;
      //timerTrampilla = millis() + TIEMPO_TRAMPILLA;
      
      // Descartamos la tarea de la cola FIFO porque ya se sanearon ambos extremos
      indiceLectura = (indiceLectura + 1) % MAX_TAREAS;
      cantidadTareas--;
    }
  }
}