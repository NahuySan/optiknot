// --- CONSTANTES DE LA RAMPA DE ACELERACIÓN ---
const int RETARDO_MAX_US = 2000;
const int RETARDO_MIN_US = 800;
const int PASOS_RAMPA = 400;

long pasosDesdeArranque = 0;
bool estadoAnteriorAvance = false;

void avanzarMotor() {
  if (modoAvance) {
    if (!estadoAnteriorAvance) {
      pasosDesdeArranque = 0;
      posicionInicioTramo = posicionAbsolutaCinta;
      estadoAnteriorAvance = true;
    }

    // 1. Calcular distancias para adaptar la rampa
    long pasosRestantes = 999999;
    long tramoTotal = 999999;

    if (cantidadTareas > 0) {
      TareaEncapsulado &tarea = colaTareas[indiceLectura];
      long proximoPaso = (!tarea.primerCorteHecho) ? tarea.pasoCorteFrontal : tarea.pasoCorteTrasero;
      pasosRestantes = proximoPaso - posicionAbsolutaCinta;
      tramoTotal = proximoPaso - posicionInicioTramo;
    }

    // 2. Definir longitud efectiva de la rampa (trapezoidal o triangular)
    long rampaEfectiva = PASOS_RAMPA;
    if (tramoTotal < (PASOS_RAMPA * 2)) {
      rampaEfectiva = tramoTotal / 2;
    }
    if (rampaEfectiva < 0) {
      rampaEfectiva = 0;
    }

    // 3. Ajuste dinámico de velocidad manteniendo aceleración constante
    int retardoActual = RETARDO_MIN_US;

    if (pasosDesdeArranque < rampaEfectiva) {
      retardoActual = map(pasosDesdeArranque, 0, PASOS_RAMPA, RETARDO_MAX_US, RETARDO_MIN_US);
    }
    else if (pasosRestantes <= rampaEfectiva && pasosRestantes > 0) {
      retardoActual = map(pasosRestantes, PASOS_RAMPA, 0, RETARDO_MIN_US, RETARDO_MAX_US);
    }

    // 4. Pulso físico
    digitalWrite(PIN_STEP, HIGH);
    delayMicroseconds(retardoActual);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds(retardoActual);

    posicionAbsolutaCinta++;
    pasosDesdeArranque++;

  } else {
    estadoAnteriorAvance = false;
  }
}

void ejecutarOdometriaYCortes() {
  if (corteEnProceso) return;

  if (cantidadTareas > 0) {
    TareaEncapsulado &tareaActual = colaTareas[indiceLectura];

    // CORTE FRONTAL
    if (!tareaActual.primerCorteHecho && posicionAbsolutaCinta >= tareaActual.pasoCorteFrontal) {
      modoAvance = false;
      iniciarCorte();
      tareaActual.primerCorteHecho = true;
    }
    // CORTE TRASERO
    else if (tareaActual.primerCorteHecho && posicionAbsolutaCinta >= tareaActual.pasoCorteTrasero) {
      modoAvance = false;
      iniciarCorte();

      // Se elimina la tarea completada de la cola FIFO
      indiceLectura = (indiceLectura + 1) % MAX_TAREAS;
      cantidadTareas--;
    }
  }
}