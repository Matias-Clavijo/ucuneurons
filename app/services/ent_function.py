def calcular_riesgo_inhalacion_ntp937(
    # Parámetros para Clase de Peligro
    frases_h: list = None,
    vla_mg_m3: float = None,
    # Parámetros para Exposición Potencial
    cantidad_g_dia: float = 0,
    clase_frecuencia: int = 0,
    # Parámetro de Volatilidad (simplificado)
    clase_volatilidad_o_pulverulencia: int = 1, # <-- PARÁMETRO NUEVO Y SIMPLIFICADO
    # Parámetros del Proceso y Protección
    clase_procedimiento: int = 4,
    clase_proteccion_colectiva: int = 4
):
    """
    Calcula la puntuación de riesgo por inhalación según la metodología NTP 937.
    Esta versión espera la 'clase_volatilidad_o_pulverulencia' (1-3) directamente.
    """

    # --- 1. DETERMINACIÓN DEL RIESGO POTENCIAL ---
    # (Esta sección permanece igual)
    clases_h = {
        'H335': 2, 'H336': 2, 'H304': 3, 'H332': 3, 'H361': 3, 'H361d': 3, 'H361f': 3, 'H361fd': 3,
        'H362': 3, 'H371': 3, 'H373': 3, 'EUH071': 3, 'H331': 4, 'H334': 4, 'H341': 4, 'H351': 4,
        'H360': 4, 'H360F': 4, 'H360FD': 4, 'H360D': 4, 'H360Df': 4, 'H360Fd': 4, 'H370': 4,
        'H372': 4, 'EUH029': 4, 'EUH031': 4, 'H330': 5, 'H340': 5, 'H350': 5, 'H350i': 5,
        'EUH032': 5, 'EUH070': 5
    }
    clase_peligro = 1
    if frases_h:
        for h in frases_h:
            if h in clases_h and clases_h[h] > clase_peligro:
                clase_peligro = clases_h[h]
    elif vla_mg_m3 is not None:
        if vla_mg_m3 <= 0.1: clase_peligro = 5
        elif vla_mg_m3 <= 1: clase_peligro = 4
        elif vla_mg_m3 <= 10: clase_peligro = 3
        elif vla_mg_m3 <= 100: clase_peligro = 2
        else: clase_peligro = 1

    if cantidad_g_dia < 100: clase_cantidad = 1
    elif cantidad_g_dia < 10000: clase_cantidad = 2
    elif cantidad_g_dia < 100000: clase_cantidad = 3
    elif cantidad_g_dia < 1000000: clase_cantidad = 4
    else: clase_cantidad = 5

    matriz_exposicion = {
        (1,0):0, (1,1):1, (1,2):1, (1,3):1, (1,4):1, (2,0):0, (2,1):2, (2,2):2, (2,3):2,
        (2,4):2, (3,0):0, (3,1):3, (3,2):3, (3,3):3, (3,4):4, (4,0):0, (4,1):3, (4,2):4,
        (4,3):4, (4,4):5, (5,0):0, (5,1):4, (5,2):5, (5,3):5, (5,4):5
    }
    clase_exposicion_potencial = matriz_exposicion.get((clase_cantidad, clase_frecuencia), 0)

    if clase_exposicion_potencial == 0:
        clase_riesgo_potencial = 0
    else:
        matriz_riesgo = {
            (1,1):1, (1,2):1, (1,3):2, (1,4):3, (1,5):4, (2,1):1, (2,2):1, (2,3):2, (2,4):3,
            (2,5):4, (3,1):1, (3,2):2, (3,3):3, (3,4):4, (3,5):5, (4,1):1, (4,2):2, (4,3):3,
            (4,4):4, (4,5):5, (5,1):2, (5,2):3, (5,3):4, (5,4):5, (5,5):5
        }
        clase_riesgo_potencial = matriz_riesgo.get((clase_exposicion_potencial, clase_peligro), 1)

    puntuaciones_riesgo = {0:0, 1: 1, 2: 10, 3: 100, 4: 1000, 5: 10000}
    p_riesgo_pot = puntuaciones_riesgo.get(clase_riesgo_potencial, 0)

    # --- 2. DETERMINACIÓN DE VOLATILIDAD O PULVERULENCIA (SIMPLIFICADO) ---
    # Se ha eliminado toda la lógica de cálculo. Ahora se usa el parámetro directamente.
    puntuaciones_vol = {1: 1, 2: 10, 3: 100}
    p_volatilidad = puntuaciones_vol.get(clase_volatilidad_o_pulverulencia, 1)

    # --- 3. DETERMINACIÓN DEL PROCEDIMIENTO DE TRABAJO ---
    puntuaciones_proc = {1: 0.001, 2: 0.05, 3: 0.5, 4: 1}
    p_procedimiento = puntuaciones_proc.get(clase_procedimiento, 1)

    # --- 4. DETERMINACIÓN DE PROTECCIÓN COLECTIVA ---
    puntuaciones_protec = {1: 0.001, 2: 0.1, 3: 0.7, 4: 1, 5: 10}
    p_protec_colec = puntuaciones_protec.get(clase_proteccion_colectiva, 1)

    # --- 5. FACTOR DE CORRECCIÓN POR VLA ---
    fc_vla = 1
    if vla_mg_m3 is not None:
        if vla_mg_m3 <= 0.001: fc_vla = 100
        elif vla_mg_m3 <= 0.01: fc_vla = 30
        elif vla_mg_m3 <= 0.1: fc_vla = 10

    # --- CÁLCULO FINAL ---
    p_inh = p_riesgo_pot * p_volatilidad * p_procedimiento * p_protec_colec * fc_vla

    if p_inh > 1000: caracterizacion = "Riesgo ALTA. Riesgo probablemente muy elevado (medidas correctoras inmediatas)"
    elif p_inh > 100: caracterizacion = "Riesgo MODERADO. Necesita probablemente medidas correctoras y/o una evaluacion mas detallada"
    elif p_inh == 0: caracterizacion = "Sin riesgo por exposición (frecuencia cero)"
    else: caracterizacion = "Riesgo BAJO. Riesgo a priori bajo"

    return {
        "p_inh": p_inh,
        "risk": caracterizacion,
        "extra": {
            "risk_class": clase_peligro,
            "risk_potential_score": p_riesgo_pot,
            "volatility_score": p_volatilidad,
            "procedure_score": p_procedimiento,
            "collective_protection_score": p_protec_colec,
            "vla_correction_factor": fc_vla,
        }
    }


