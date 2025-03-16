import numpy as np
from scipy.optimize import differential_evolution
import numpy_financial as npf
from simulator import setup_simulator  # Import the simulator setup function

# Constants
TASA_LIBRE_DE_RIESGO = 0.015  # Risk-free rate
RETORNO_MERCADO = 0.08  # Market return
BETA_APALANCADO = 1.2  # Leveraged beta
TASA_CRECIMIENTO_PERPETUIDAD = 0.02  # Perpetual growth rate
HORIZON = 6  # Fixed time horizon in years

def calcular_metricas(variables, country_data):
    """
    Calculate financial metrics for the project with dynamic funding rate, hedging cost, corporate tax, and risk-adjusted profit.

    Args:
        variables (tuple): Tuple containing:
                           - variables[0]: Factoring discount (%).
                           - variables[1]: Principal percentage (%).
                           - variables[2]: Markup for funding rate (%).
                           - variables[3]: Interest rate charged to shrimp farmers (%).
        country_data (dict): Dictionary containing country-specific data:
                            - 'annual_hedging_cost': Hedging cost for the country.
                            - 'corporate_tax': Corporate tax rate for the country.
                            - 'risk_adjusted_profit': Risk-adjusted profit for the country.
                            - 'base_interest_rate': Base interest rate for the country (%).

    Returns:
        dict: A dictionary containing the calculated financial metrics.
    """

def calcular_metricas(variables, country_data):
    descuento_factoring, porcentaje_principal, markup, tasa_camaronero = variables
    hedging_cost = country_data.get('Annualized Coverage Cost (%)', 0) / 100
    corporate_tax = country_data.get('Corporate Tax (%)', 0) / 100  # Already in %, convert to decimal
    risk_adjusted_profit = country_data.get('Adjusted Profitability (%)', 0) / 100
    base_interest_rate = country_data.get('Base Loan Rate (%)', 0.5) / 100

    # Validate input ranges
    if not (10 <= descuento_factoring <= 20 and 15 <= porcentaje_principal <= 30 and
            4 <= markup <= 6 and 12 <= tasa_camaronero <= 14):
        print(f"Invalid params: {variables}")
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0,
            'monto_financiado': 0, 'tasa_financiamiento_anual': 0, 'costo_inicial': 0, 'corporate_tax': corporate_tax
        }

    # Convert percentages to decimals
    descuento_factoring /= 100
    porcentaje_principal /= 100
    markup /= 100
    tasa_camaronero_anual = tasa_camaronero / 100

    # Calculate initial investment and financing
    RECEBIBLES_INICIALES = 120_000
    costo_inicial = RECEBIBLES_INICIALES * (1 - descuento_factoring)
    principal = costo_inicial * porcentaje_principal
    capital_propio = costo_inicial - principal
    monto_financiado = costo_inicial - principal

    if capital_propio <= 0:
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0,
            'monto_financiado': 0, 'tasa_financiamiento_anual': 0, 'costo_inicial': 0, 'corporate_tax': corporate_tax
        }

    # Calculate funding rate
    tasa_financiamiento_anual = base_interest_rate + markup + hedging_cost

    # Calculate total financing cost and income
    costo_financiamiento_total = monto_financiado * tasa_financiamiento_anual * HORIZON
    ingreso_intereses_totales = monto_financiado * tasa_camaronero_anual * HORIZON
    utilidad_antes_de_impuestos = ingreso_intereses_totales - costo_financiamiento_total

    if utilidad_antes_de_impuestos <= 0:
        return {
            'roi': -np.inf, 'roe': -np.inf, 'payback': np.inf, 'irr': -np.inf, 'npv': -np.inf, 'pi': -np.inf,
            'rate_difference': np.inf, 'valid': False, 'utilidad_despues_de_impuestos': 0, 'capital_propio': 0,
            'monto_financiado': 0, 'tasa_financiamiento_anual': 0, 'costo_inicial': 0, 'corporate_tax': corporate_tax
        }

    # Calculate taxes and after-tax profit
    impuestos = utilidad_antes_de_impuestos * corporate_tax
    utilidad_despues_de_impuestos = utilidad_antes_de_impuestos - impuestos

    # Calculate financial metrics
    roi = utilidad_despues_de_impuestos / costo_inicial if costo_inicial != 0 else 0
    roe = utilidad_despues_de_impuestos / capital_propio if capital_propio != 0 else np.inf
    payback = costo_inicial / utilidad_despues_de_impuestos if utilidad_despues_de_impuestos != 0 else np.inf

    flujos_caja = [utilidad_despues_de_impuestos] * HORIZON
    flujo_caja_array = np.insert(flujos_caja, 0, -costo_inicial)
    irr_value = npf.irr(flujo_caja_array)
    npv_value = npf.npv(tasa_financiamiento_anual, flujo_caja_array)

    pv_flujos_caja_entrantes = np.sum([flujos_caja[t] / (1 + tasa_financiamiento_anual) ** (t + 1) for t in range(HORIZON)])
    pi_value = (pv_flujos_caja_entrantes + costo_inicial) / costo_inicial if costo_inicial != 0 else np.inf

    rate_difference = abs(tasa_camaronero_anual - tasa_financiamiento_anual)  # Already decimal in calcular_metricas

    return {
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
        'tasa_financiamiento_anual': tasa_financiamiento_anual,
        'costo_inicial': costo_inicial,
        'corporate_tax': corporate_tax  # Include for DCF
    }

def objetivo_combinado(variables, country_data):
    """
    Combined objective function for optimization. Penalizes invalid solutions and those that do not meet
    the target ranges for financial metrics. Minimizes the difference between the shrimp farmer's interest rate
    and the funding rate.

    Args:
        variables (tuple): Tuple containing the factoring discount, principal percentage, markup, and shrimp farmer rate.
        country_data (dict): Dictionary containing country-specific data.

    Returns:
        float: Value of the objective function. Returns np.inf if the solution is invalid or does not meet constraints.
               Returns the rate difference if the solution is valid and meets constraints.
    """
def objetivo_combinado(variables, country_data):
    metricas = calcular_metricas(variables, country_data)

    if not metricas['valid']:
        return np.inf  # Invalid parameters

    penalizacion = 0
    # Enforce target ranges
    if not 0.20 <= metricas['irr'] <= 0.30:
        print(f"IRR {metricas['irr']:.2%} outside 20-30% for {variables}")
        penalizacion += 1000  # Increase penalty to force compliance
    if metricas['pi'] <= 1:
        penalizacion += 1000
    if metricas['npv'] <= 0:
        penalizacion += 1000
    if not 0.10 <= metricas['roe'] <= 0.15:
        penalizacion += 1000
    if not 0.20 <= metricas['roi'] <= 0.30:
        penalizacion += 1000
    if metricas['payback'] > HORIZON:
        penalizacion += 1000

    if penalizacion > 0:
        return penalizacion + metricas['rate_difference']  # Combine penalty with rate diff

    return metricas['rate_difference']  # Minimize this only if no penalties

def optimize_for_country(country_data):
    mapped_data = {
        'annual_hedging_cost': country_data.get('Annualized Coverage Cost (%)', 0),
        'corporate_tax': country_data.get('Corporate Tax (%)', 0),
        'risk_adjusted_profit': country_data.get('Adjusted Profitability (%)', 0),
        'base_interest_rate': country_data.get('Base Loan Rate (%)', 0.5)
    }
    print(f"Optimizing for {country_data['Country']}: {mapped_data}")  # Debug

    bounds = [(10, 20), (15, 30), (4, 6), (12, 14)]
    resultado = differential_evolution(
        objetivo_combinado,
        bounds,
        args=(mapped_data,),
        strategy='best1bin',
        maxiter=1000,
        popsize=15,
        tol=0.001,
        mutation=(0.5, 1),
        recombination=0.7,
        seed=42
    )
    
    variables_optimas = resultado.x
    metricas_optimas = calcular_metricas(variables_optimas, mapped_data)
    print(f"Result for {country_data['Country']}: IRR={metricas_optimas['irr']:.2%}, Rate Diff={metricas_optimas['rate_difference']:.4f}")
    return {
        'variables_optimas': variables_optimas,
        'metricas_optimas': metricas_optimas,
        'diferencia_tasas_minimizada': resultado.fun
    }

def print_optimization_results(results, country_name):
    print(f"\n{'='*50}")
    print(f"Optimal Parameters for {country_name.upper()}")
    print(f"{'='*50}")
    print(f"- Factoring Discount: {results['variables_optimas'][0]:.2f}%")
    print(f"- Principal Percentage: {results['variables_optimas'][1]:.2f}%")
    print(f"- Funding Markup: {results['variables_optimas'][2]:.2f}%")
    print(f"- Farmer Interest Rate: {results['variables_optimas'][3]:.2f}%")
    
    print(f"\nKey Financial Metrics:")
    print(f"- ROI: {results['metricas_optimas']['roi']:.2%}")
    print(f"- ROE: {results['metricas_optimas']['roe']:.2%}")
    print(f"- Payback Period: {results['metricas_optimas']['payback']:.2f} years")
    print(f"- IRR: {results['metricas_optimas']['irr']:.2%}")
    print(f"- NPV: ${results['metricas_optimas']['npv']:,.2f}")
    print(f"- Profitability Index: {results['metricas_optimas']['pi']:.2f}")
    print(f"- Rate Spread: {results['metricas_optimas']['rate_difference']:.4f}")  # Use internal rate_difference

def analyze_top_opportunities(all_results, top_n=10):
    """Analyze and display top performing country opportunities."""
    # Filter valid results and sort by NPV
    valid_results = [r for r in all_results if r['metricas_optimas']['valid']]
    sorted_results = sorted(valid_results, 
                          key=lambda x: x['metricas_optimas']['npv'], 
                          reverse=True)[:top_n]

    print(f"\n{'#'*50}")
    print(f"TOP {top_n} ARBITRAGE OPPORTUNITIES")
    print(f"{'#'*50}")
    
    for i, result in enumerate(sorted_results, 1):
        print(f"\n#{i} {result['country'].upper()}")
        print(f"NPV: ${result['metricas_optimas']['npv']:,.2f} | IRR: {result['metricas_optimas']['irr']:.2%}")
        print(f"ROE: {result['metricas_optimas']['roe']:.2%} | Rate Spread: {result['diferencia_tasas_minimizada']:.4f}")
        print(f"Params: Factoring {result['variables_optimas'][0]:.1f}%, "
              f"Principal {result['variables_optimas'][1]:.1f}%, "
              f"Markup {result['variables_optimas'][2]:.1f}%")

def optimize_and_analyze():
    simulator = setup_simulator()
    aerator_price = 1158
    aerator_quantity = 100
    client_rate = 0.12
    horizon = 6
    factoring_discount = 0.10
    loan_markup = 2.0

    # Get country data from simulator
    _, arbitrage_df = simulator.analyze_opportunities(  # Unpack the tuple
        aerator_price=aerator_price,
        aerator_quantity=aerator_quantity,
        client_rate=client_rate,
        horizon=horizon,
        factoring_discount=factoring_discount,
        loan_markup=loan_markup
    )
    
    all_results = []
    # Convert DataFrame to list of dicts and process each country
    for country_data in arbitrage_df.to_dict(orient='records')[:10]: 
        print(f"Processing {country_data.get('Country', 'Unknown')}: {country_data}") # Use DataFrame rows
        try:
            result = optimize_for_country(country_data)
            result['country'] = country_data['Country']  # Match simulator's key
            all_results.append(result)
            print_optimization_results(result, country_data['Country'])
        except Exception as e:
            print(f"Error processing {country_data.get('Country', 'Unknown')}: {str(e)}")
            continue
    
    analyze_top_opportunities(all_results)
    return all_results

# Updated DCF reporting
def print_dcf_analysis(metricas_optimas):
    print("Metrics received:", metricas_optimas)
    """Enhanced DCF analysis reporting."""
    print(f"\n{'='*50}")
    print("DCF VALUATION ANALYSIS")
    print(f"{'='*50}")
    
    # Calculate WACC components
    costo_capital_propio = TASA_LIBRE_DE_RIESGO + BETA_APALANCADO * (RETORNO_MERCADO - TASA_LIBRE_DE_RIESGO)
    costo_deuda_despues_impuestos = metricas_optimas['tasa_financiamiento_anual'] * (1 - metricas_optimas['corporate_tax'])
    
    print("\nCost of Capital Components:")
    print(f"- Cost of Equity (CAPM): {costo_capital_propio:.2%}")
    print(f"- After-tax Cost of Debt: {costo_deuda_despues_impuestos:.2%}")
    
    # Print final valuation
    print(f"\nEnterprise Value: ${metricas_optimas.get('valor_empresa', 0):,.2f}")
    print(f"Equity Value: ${metricas_optimas.get('valor_capital_propio', 0):,.2f}")

# Example execution
if __name__ == "__main__":
    final_results = optimize_and_analyze()
    
    # Add DCF analysis for best result
    if final_results:
        best_result = max(final_results, key=lambda x: x['metricas_optimas']['npv'])
        print_dcf_analysis(best_result['metricas_optimas'])