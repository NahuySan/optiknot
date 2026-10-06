"""
Módulo de procesamiento geométrico y visión artificial.
Contiene las funciones necesarias para depurar las lecturas de OpenCV.
"""

def agrupar_defectos_cercanos(cajas, distancia_minima):
    # Si la lista de cajas está vacía, retornamos una lista vacía para no procesar nada
    if not cajas: return []
    
    # Ordenamos las cajas detectadas por su coordenada Y (de arriba hacia abajo en la imagen)
    cajas.sort(key=lambda b: b[1])
    
    # Inicializamos la lista de cajas agrupadas tomando la primera caja ordenada
    cajas_agrupadas = [cajas[0]]
    
    # Iteramos sobre el resto de las cajas detectadas para verificar solapamientos o cercanías
    for caja_actual in cajas[1:]:
        # Tomamos la última caja que validamos e ingresamos a nuestro grupo consolidado
        caja_anterior = cajas_agrupadas[-1]
        
        # Desempaquetamos coordenadas X, Y, ancho y alto de la caja anterior
        x_ant, y_ant, w_ant, h_ant = caja_anterior
        # Desempaquetamos coordenadas X, Y, ancho y alto de la caja que estamos evaluando
        x_act, y_act, w_act, h_act = caja_actual
        
        # Calculamos la distancia vertical libre entre el fin de la caja anterior y el inicio de la actual
        distancia_y = y_act - (y_ant + h_ant)
        
        # Si esta separación vertical es menor a nuestra tolerancia (distancia_minima), las unificamos
        if distancia_y < distancia_minima:
            # El nuevo inicio en Y es el punto más alto entre ambas cajas
            nuevo_y = min(y_ant, y_act)
            # La nueva altura cubre hasta el punto más bajo (Y + H) de ambas cajas restando el nuevo origen Y
            nuevo_h = max(y_ant + h_ant, y_act + h_act) - nuevo_y
            # El nuevo inicio en X es el punto más a la izquierda entre ambas
            nuevo_x = min(x_ant, x_act)
            # El nuevo ancho cubre hasta el extremo derecho (X + W) de ambas restando el nuevo origen X
            nuevo_w = max(x_ant + w_ant, x_act + w_act) - nuevo_x
            
            # Reemplazamos la última caja de la lista con esta nueva macro-caja fusionada
            cajas_agrupadas[-1] = (nuevo_x, nuevo_y, nuevo_w, nuevo_h)
        else:
            # Si la separación es suficientemente amplia, la consideramos un defecto independiente y la agregamos
            cajas_agrupadas.append(caja_actual)
            
    # Retornamos la lista final con los defectos depurados y unificados
    return cajas_agrupadas