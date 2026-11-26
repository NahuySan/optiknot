void leerSerial() {
  // Serial.available() devuelve la cantidad de bytes que están esperando en el buffer de hardware del Arduino.
  // Usamos un 'while' en lugar de un 'if' para procesar de golpe todos los caracteres que hayan llegado
  // en los milisegundos que el microcontrolador estuvo ocupado moviendo la cinta.
  while (Serial.available() > 0) {
    
    // Leemos estrictamente UN solo byte (caracter) del buffer. 
    // Esto es instantáneo (microsegundos) y no bloquea el procesador.
    char c = Serial.read();
    
    // Evaluamos si el caracter que acaba de entrar es el salto de línea ('\n').
    // El '\n' es nuestra bandera; nos avisa que el script de Python terminó de mandar la trama completa.
    if (c == '\n') {
      
      // Limpiamos la trama de cualquier espacio en blanco, tabulación o retorno de carro ('\r')
      // que suele colarse al final de las comunicaciones seriales y arruina las comparaciones.
      tramaSerial.trim();
      
      // Verificamos si la trama es el comando de arranque de la máquina.
      if (tramaSerial == "A") {
        modoAvance = true;                     // Habilita la máquina de estados principal.
        //digitalWrite(PIN_LED_MOTOR, HIGH);     // Enciende el piloto en el tablero.
      }

    else if (tramaSerial == "R") {
    // --- SENSOR VIRTUAL DETECTÓ NUEVA TABLA ---
    posicionAbsolutaCinta = 0; // Reseteamos el contador de pasos al milímetro cero
    posicionInicioTramo = 0;
    // Limpiamos la memoria de cortes viejos.
    // Si la tabla anterior salió antes de terminar un corte por X motivo, 
    // vaciamos la cola FIFO para que no tale la tabla nueva por error.
    cantidadTareas = 0;
    indiceLectura = 0;
    indiceEscritura = 0;
  } 
      
      // Si no es un arranque, verificamos si es una trama de coordenadas de corte ("Q:").
      else if (tramaSerial.startsWith("Q:")) {
        
        // Buscamos en qué posición (índice numérico) está la barra vertical '|'
        // que separa el corte frontal del corte trasero (ej: "Q:1500|2100").
        int separador = tramaSerial.indexOf('|');
        
        // VALIDACIÓN CRÍTICA: indexOf devuelve -1 si no encuentra el caracter '|'.
        // Si entra ruido electromagnético y la trama llega rota, esto evita que el código 
        // intente procesar datos inexistentes, lo cual colgaría el microcontrolador.
        if (separador != -1) {
          
          // Extraemos los números. substring(2, separador) corta desde el índice 2 (después de "Q:")
          // hasta donde está la barra '|'. toInt() convierte ese texto en un número entero largo.
          long pasoRelativoFrontal = tramaSerial.substring(2, separador).toInt();
          long pasoRelativoTrasero = tramaSerial.substring(separador + 1).toInt();
          
          // Verificamos que la cola FIFO tenga espacio antes de guardar la tarea.
          if (cantidadTareas < MAX_TAREAS) {
            
            // CONVERSIÓN ODOMÉTRICA: Pasamos de coordenadas relativas (lo que ve la cámara en ese instante)
            // a coordenadas absolutas (los pasos totales que dio el motor desde que arrancó la máquina).
            colaTareas[indiceEscritura].pasoCorteFrontal = posicionAbsolutaCinta + pasoRelativoFrontal;
            colaTareas[indiceEscritura].pasoCorteTrasero = posicionAbsolutaCinta + pasoRelativoTrasero;
            
            // Inicializamos el flag de estado para esta tarea específica.
            colaTareas[indiceEscritura].primerCorteHecho = false;
            
            // LÓGICA DE BUFFER CIRCULAR: Incrementamos el índice de escritura.
            // El operador módulo '%' hace que si indiceEscritura llega a 10 (MAX_TAREAS), 
            // la cuenta vuelva automáticamente a 0. Así sobreescribimos los espacios ya leídos.
            indiceEscritura = (indiceEscritura + 1) % MAX_TAREAS;
            
            // Aumentamos el contador global de tareas pendientes.
            cantidadTareas++;
          }
        }
      }
      
      // Como ya procesamos el mensaje completo (sea "A" o "Q:"), vaciamos la variable global
      // para que esté limpia y lista para empezar a concatenar la siguiente trama.
      tramaSerial = ""; 
    } 
    else {
      // Si el caracter leído NO es un salto de línea ('\n'), significa que la trama está por la mitad.
      // Simplemente lo agregamos al final del string y salimos de la función rápidamente 
      // para que el motor pueda dar el siguiente paso sin frenarse.
      tramaSerial += c;
    }
  }
}
void enviarTelemetria() {
  unsigned long tiempoActual = millis();

  if (tiempoActual - timerTelemetria >= INTERVALO_TELEMETRIA_MS) {
    timerTelemetria = tiempoActual;
    Serial.print("ODOM:");
    Serial.println(posicionAbsolutaCinta);
  }
}