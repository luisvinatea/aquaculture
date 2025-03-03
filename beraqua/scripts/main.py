# main.py
import logging
from cleaner import ProcesadorCSV
from loader import AnalizadorArbitraje
from calculator import AnalizadorOportunidadesArbitraje
from simulator import setup_simulator
from IPython.display import display

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
directorio_datos = "/home/luisvinatea/Dev/Repos/aquaculture/beraqua/notebooks/datasets/indicators/forex"
directorio_ecuador = "/home/luisvinatea/Dev/Repos/aquaculture/beraqua/notebooks/datasets/shrimp_industry/ecuador"
ruta_currency_tickers_csv = "/home/luisvinatea/Dev/Repos/aquaculture/beraqua/notebooks/datasets/indicators/forex/currency_tickers.csv"
shapefile_path = "/home/luisvinatea/Dev/Repos/aquaculture/beraqua/data/shapefiles/ne_110m_admin_0_countries.shp"

def run_pipeline():
    # Step 1: Clean and process data
    logging.info("Starting data cleaning...")
    procesador = ProcesadorCSV(directorio_datos, ruta_currency_tickers_csv, shapefile_path)
    procesador.procesar_archivos()

    # Step 2: Load data
    logging.info("Loading data...")
    analizador_loader = AnalizadorArbitraje(directorio_datos, directorio_ecuador)
    analizador_loader.cargar_datos()

    # Step 3: Calculate arbitrage opportunities
    logging.info("Calculating arbitrage opportunities...")
    analizador_calc = AnalizadorOportunidadesArbitraje(directorio_datos, directorio_ecuador)
    resultados_arbitraje = analizador_calc.analizar_paises(tasa_cliente=12.0, horizonte=6)
    logging.info(f"Top arbitrage opportunity: {resultados_arbitraje[0]['pais']} with {resultados_arbitraje[0]['beneficio_ajustado_riesgo_te_ajustado']}%")

    # Step 4: Launch interactive simulation
    logging.info("Launching interactive simulation...")
    widgets = setup_simulator()
    for widget in widgets.values():
        display(widget)

if __name__ == "__main__":
    run_pipeline()