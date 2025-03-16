import numpy as np
from scipy.optimize import differential_evolution
import numpy_financial as npf

def calcular_metricas_parametros_fijos(variables):
    """
    Calcula las métricas financieras del proyecto con parámetros de descuento de factoring
    y porcentaje principal del camaronero fijos.

    Args:
        variables (tuple): Tupla que contiene el markup (en porcentaje) y la tasa de interés al camaronero (en porcentaje).
                           - variables[0]: Markup para la tasa de financiamiento suiza (%).
                           - variables[1]: Tasa de interés anual cobrada a los camaroneros (%).

    Returns:
        dict: Un diccionario que contiene las métricas financieras calculadas:
              - 'roi': Retorno sobre la Inversión (ROI).
              - 'roe': Retorno sobre el Capital Propio (ROE).
              - 'payback': Tiempo de recuperacion de la inversion (en años).
              - 'irr': Tasa Interna de Retorno (TIR).
              - 'npv': Valor Presente Neto (VPN).
              - 'pi': Índice de Rentabilidad (IR).
              - 'rate_difference': Diferencia absoluta entre la tasa de interés al camaronero y la tasa suiza.
              - 'valid': Booleano que indica si el conjunto de parámetros es válido (True) o no (False).
              - 'utilidad_despues_de_impuestos': Utilidad después de impuestos calculada.
              - 'capital_propio': Capital propio invertido.
              - 'monto_financiado': Monto total financiado.
              - 'tasa_suiza_anual': Tasa de interés suiza anual utilizada en el cálculo.
              - 'costo_inicial': Costo inicial de la inversión.
    """
    markup, tasa_camaronero = variables
    descuento_factoring = 0.10  # Fijo en 10%
    porcentaje_principal = 0.25   # Fijo en 25%
    periodo_pago_camaronero_meses = 72 # Periodo de pago del camaronero en meses
    TASA_BASE_SUIZA_ANUAL = 0.005 # Tasa base anual en Suiza
    COSTO_HEDGING_ANUAL = -0.00036 # Costo anual de cobertura (hedging)
    TASA_IMPUESTOS = 0.146 # Tasa de impuestos
    RECEBIBLES_INICIALES = 120_000 # Monto inicial de cuentas por cobrar

    markup /= 100 # Convertir markup de porcentaje a decimal
    tasa_camaronero_anual = tasa_camaronero / 100 # Convertir tasa camaronero de porcentaje a decimal

    # Validar rangos de parámetros de entrada
    if not (0.04 <= markup <= 0.06 and 0.12 <= tasa_camaronero_anual <= 0.14):
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0, 'monto_financiado': 0, 'tasa_suiza_anual': 0, 'costo_inicial': 0
        }

    periodo_años = periodo_pago_camaronero_meses / 12 # Periodo de pago en años
    costo_inicial = RECEBIBLES_INICIALES * (1 - descuento_factoring) # Costo inicial de la inversión
    principal = costo_inicial * porcentaje_principal # Monto del principal
    capital_propio = costo_inicial - principal # Capital propio invertido
    if capital_propio <= 0:
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0, 'monto_financiado': 0, 'tasa_suiza_anual': 0, 'costo_inicial': 0
        }

    monto_financiado = costo_inicial - principal # Monto financiado externamente
    tasa_suiza_anual = TASA_BASE_SUIZA_ANUAL + markup + COSTO_HEDGING_ANUAL # Tasa de financiamiento suiza anual
    costo_financiamiento_total = monto_financiado * tasa_suiza_anual * periodo_años # Costo total de financiamiento
    ingreso_intereses_totales = monto_financiado * tasa_camaronero_anual * periodo_años # Ingreso total por intereses cobrados
    utilidad_antes_de_impuestos = ingreso_intereses_totales - costo_financiamiento_total # Utilidad antes de impuestos

    if utilidad_antes_de_impuestos <= 0:
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0, 'monto_financiado': 0, 'tasa_suiza_anual': 0, 'costo_inicial': 0
        }

    impuestos = utilidad_antes_de_impuestos * TASA_IMPUESTOS # Calculo de impuestos
    utilidad_despues_de_impuestos = utilidad_antes_de_impuestos - impuestos # Utilidad despues de impuestos

    # Cálculo de métricas financieras
    roi = utilidad_despues_de_impuestos / costo_inicial if costo_inicial != 0 else 0 # ROI
    roe = utilidad_despues_de_impuestos / capital_propio if capital_propio != 0 else np.inf # ROE
    payback = costo_inicial / utilidad_despues_de_impuestos if utilidad_despues_de_impuestos != 0 else np.inf # Payback

    inversion_inicial = costo_inicial # Inversión inicial
    flujos_caja = [utilidad_despues_de_impuestos] * 6 # Flujos de caja
    flujo_caja_array = np.insert(flujos_caja, 0, -inversion_inicial) # Array de flujos de caja incluyendo la inversión inicial
    irr_value = npf.irr(flujo_caja_array) # TIR
    npv_value = npf.npv(tasa_suiza_anual, flujo_caja_array) # VPN

    pv_flujos_caja_entrantes = np.sum([flujos_caja[t] / (1 + tasa_suiza_anual)**(t+1) for t in range(len(flujos_caja))]) # Valor presente de flujos de caja entrantes
    pi_value = (pv_flujos_caja_entrantes + inversion_inicial) / inversion_inicial if inversion_inicial != 0 else np.inf # IR

    rate_difference = abs(tasa_camaronero_anual - tasa_suiza_anual) # Diferencia de tasas

    metricas = {
        'roi': roi,
        'roe': roe,
        'payback': payback,
        'irr': irr_value,
        'npv': npv_value,
        'pi': pi_value,
        'rate_difference': rate_difference,
        'valid': True,
        'utilidad_despues_de_impuestos': utilidad_despues_de_impuestos,
        'capital_propio': capital_propio,
        'monto_financiado': monto_financiado,
        'tasa_suiza_anual': tasa_suiza_anual,
        'costo_inicial': costo_inicial
    }
    return metricas

def objetivo_combinado_parametros_fijos(variables):
    """
    Función objetivo combinada para la optimización, penaliza soluciones inválidas
    y aquellas que no cumplen con los rangos objetivo de las métricas financieras.
    Minimiza la diferencia entre la tasa de interés al camaronero y la tasa suiza.

    Args:
        variables (tuple): Tupla que contiene el markup y la tasa de interés al camaronero.

    Returns:
        float: Valor de la función objetivo. Retorna np.inf si la solución no es válida o no cumple las restricciones.
               Retorna la diferencia de tasas si la solución es válida y cumple las restricciones.
    """
    markup, tasa_camaronero = variables
    metricas_objetivo = calcular_metricas_parametros_fijos(variables)

    if not metricas_objetivo['valid']:
        return np.inf  # Penalización alta para conjuntos de parámetros inválidos

    penalizacion = 0 # Inicializar penalización

    # Penalizar soluciones que no cumplen con los rangos objetivo
    if not 0.20 <= metricas_objetivo['irr'] <= 0.30:
        penalizacion += 100  # Penalización sustancial por TIR fuera de rango
    if metricas_objetivo['pi'] <= 1:
        penalizacion += 100  # Penalización sustancial por IR menor o igual a 1
    if metricas_objetivo['npv'] <= 0:
        penalizacion += 100  # Penalización sustancial por VPN menor o igual a 0
    if not 0.10 <= metricas_objetivo['roe'] <= 0.15:
        penalizacion += 100  # Penalización sustancial por ROE fuera de rango
    if not 0.20 <= metricas_objetivo['roi'] <= 0.30:
        penalizacion += 100  # Penalización sustancial por ROI fuera de rango
    if metricas_objetivo['payback'] > 6:
        penalizacion += 100 # Penalización sustancial por Payback mayor a 6 años

    if penalizacion > 0:
        return penalizacion # Retornar la penalización combinada si alguna restricción no se cumple

    return metricas_objetivo['rate_difference'] # Minimizar la diferencia de tasas si se cumplen todos los objetivos


# Definir límites (bounds) para la optimización de markup y tasa_camaronero
limites_parametros_fijos = [(4, 6), (12, 14)] # Límites para markup y tasa_camaronero (rangos en porcentaje)

# Optimización utilizando el algoritmo de evolución diferencial
resultado_fijo = differential_evolution(
    objetivo_combinado_parametros_fijos, # Función objetivo a minimizar
    limites_parametros_fijos,           # Límites de los parámetros
    strategy='best1bin',                # Estrategia de evolución diferencial
    maxiter=1000,                       # Número máximo de iteraciones
    popsize=15,                         # Tamaño de la población en cada iteración
    tol=0.001,                          # Tolerancia para la convergencia
    mutation=(0.5, 1),                  # Rango de mutación
    recombination=0.7,                  # Probabilidad de recombinación
    seed=42                             # Semilla para la reproducibilidad
)

# Extraer resultados de la optimización
variables_optimas_fijas = resultado_fijo.x # Valores óptimos de markup y tasa_camaronero
diferencia_tasas_minimizada = resultado_fijo.fun # Valor mínimo de la diferencia de tasas alcanzado
metricas_optimas_fijas = calcular_metricas_parametros_fijos(variables_optimas_fijas) # Métricas financieras con parámetros óptimos

# Imprimir resultados de la optimización
print(f"""
Parámetros Óptimos para Minimizar la Diferencia de Tasas (con Descuento de Factoring y Principal del Camaronero Fijos) para cumplir con los Objetivos:
- Markup: {variables_optimas_fijas[0]:.2f}%
- Tasa de Interés al Camaronero (Anual): {variables_optimas_fijas[1]:.2f}%
- Descuento de Factoring (Fijo): 10.00%
- Principal del Camaronero (Fijo): 25.00%

Diferencia de Tasas Minimizada: {diferencia_tasas_minimizada:.4f}

Métricas Alcanzadas:
- ROI: {metricas_optimas_fijas['roi']:.2%}
- ROE: {metricas_optimas_fijas['roe']:.2%}
- Payback Time: {metricas_optimas_fijas['payback']:.2f} años
- TIR: {metricas_optimas_fijas['irr']:.2%}
- VPN: ${metricas_optimas_fijas['npv']:,.2f}
- IR: {metricas_optimas_fijas['pi']:.2f}

Rangos Objetivo de las Métricas:
- TIR: 20% - 30%
- IR: > 1
- VPN: > 0
- ROE: 10% - 15%
- ROI: 20% - 30%
- Payback Time: <= 6 años
""")

# --- Cálculo del Modelo de Flujo de Caja Descontado (DCF) ---

# Parámetros asumidos para el DCF
TASA_CRECIMIENTO_PERPETUIDAD = 0.02 # Tasa de crecimiento a perpetuidad
TASA_LIBRE_DE_RIESGO = 0.015 # Tasa libre de riesgo
RETORNO_MERCADO = 0.08 # Retorno esperado del mercado
BETA_APALANCADO = 1.2 # Beta apalancado

# Extraer valores relevantes de las métricas óptimas
utilidad_despues_de_impuestos_anio1 = metricas_optimas_fijas['utilidad_despues_de_impuestos'] # Utilidad después de impuestos del primer año (proxy para FCF)
capital_propio_optimizado = metricas_optimas_fijas['capital_propio'] # Capital propio óptimo
monto_financiado_optimizado = metricas_optimas_fijas['monto_financiado'] # Monto financiado óptimo
tasa_suiza_anual_optima = metricas_optimas_fijas['tasa_suiza_anual'] # Tasa suiza óptima
TASA_IMPUESTOS_DEF = 0.146 # Tasa de impuestos

# Calcular el Costo del Capital Propio (Ke) utilizando CAPM
costo_capital_propio = TASA_LIBRE_DE_RIESGO + BETA_APALANCADO * (RETORNO_MERCADO - TASA_LIBRE_DE_RIESGO)

# Calcular el Costo de la Deuda (Kd) después de impuestos
costo_deuda_antes_de_impuestos = tasa_suiza_anual_optima # Costo de la deuda antes de impuestos es la tasa suiza
costo_deuda_despues_de_impuestos = costo_deuda_antes_de_impuestos * (1 - TASA_IMPUESTOS_DEF) # Costo de la deuda después de impuestos

# Calcular las Ponderaciones de la Estructura de Capital
capital_total = capital_propio_optimizado + monto_financiado_optimizado # Capital total
ponderacion_capital_propio = capital_propio_optimizado / capital_total if capital_total != 0 else 0 # Ponderación del capital propio
ponderacion_deuda = monto_financiado_optimizado / capital_total if capital_total != 0 else 0 # Ponderación de la deuda

# Calcular el WACC (Costo Promedio Ponderado de Capital)
WACC = (ponderacion_capital_propio * costo_capital_propio) + (ponderacion_deuda * costo_deuda_despues_de_impuestos)

# Calcular el Valor de la Empresa (Enterprise Value - EV) utilizando el modelo de crecimiento perpetuo
if WACC <= TASA_CRECIMIENTO_PERPETUIDAD:
    valor_empresa = np.inf # Evitar división por cero o denominador negativo
else:
    valor_empresa = utilidad_despues_de_impuestos_anio1 * (1 + TASA_CRECIMIENTO_PERPETUIDAD) / (WACC - TASA_CRECIMIENTO_PERPETUIDAD)

# Calcular el Valor del Capital Propio (Equity Value)
valor_capital_propio = valor_empresa - monto_financiado_optimizado

# Imprimir resultados del modelo DCF
print(f"""

--- Modelo de Flujo de Caja Descontado (DCF) ---

Supuestos:
- Tasa de Crecimiento a Perpetuidad: {TASA_CRECIMIENTO_PERPETUIDAD:.2%}
- Tasa Libre de Riesgo: {TASA_LIBRE_DE_RIESGO:.2%}
- Retorno del Mercado: {RETORNO_MERCADO:.2%}
- Beta Apalancado: {BETA_APALANCADO:.1f}

Valores Calculados:
- Utilidad Después de Impuestos Año 1 (Proxy FCF): ${utilidad_despues_de_impuestos_anio1:,.2f}
- Costo del Capital Propio (Ke): {costo_capital_propio:.2%}
- Costo de la Deuda (Después de Impuestos) (Kd): {costo_deuda_despues_de_impuestos:.2%}
- Ponderación del Capital Propio: {ponderacion_capital_propio:.2%}
- Ponderación de la Deuda: {ponderacion_deuda:.2%}
- WACC: {WACC:.2%}

Valoración:
- Valor de la Empresa (EV): ${valor_empresa:,.2f}
- Valor del Capital Propio: ${valor_capital_propio:,.2f}
""")
