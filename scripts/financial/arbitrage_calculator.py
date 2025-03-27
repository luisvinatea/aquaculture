import os
import pandas as pd
import logging
import json
from scripts.financial.hedging_calculator import HedgingCostCalculator  # Import the HedgingCostCalculator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ArbitrageAnalyzer:
    def __init__(self, data_directory, forward_proxy_path, inflation_proxy_path, loan_margin_percentage=6.0):
        self.data_directory = data_directory
        self.forward_proxy_path = forward_proxy_path
        self.inflation_proxy_path = inflation_proxy_path
        self.loan_margin_percentage = loan_margin_percentage
        self.country_metadata = None
        self.hedging_calculator = HedgingCostCalculator(inflation_proxy_path, forward_proxy_path, verbose=False)
        self.load_data()

    def load_data(self):
        try:
            metadata_path = os.path.join(self.data_directory, "country_metadata_summary.json")
            with open(metadata_path, 'r') as f:
                self.country_metadata = json.load(f)
        except Exception as e:
            logging.error(f"Data loading failed. Check file paths and formats. Error: {e}")
            raise

    def analyze_opportunities(self, client_rate, horizon, loan_markup):
        opportunities = []
        for country, data in self.country_metadata.items():
            if country.lower() == "ecuador":
                continue

            currency_ticker = data.get("currency_ticker")
            if not currency_ticker:
                continue

            currency_pair = f"usd_{currency_ticker.lower()}"
            interest_rate = data.get("interest_rate")
            corporate_tax = data.get("corporate_tax")
            inflation_rate = data.get("inflation_rate")
            risk_rating = data.get("te")

            if any(pd.isna(v) for v in [interest_rate, corporate_tax, inflation_rate, risk_rating]):
                continue

            interest_rate_decimal = float(interest_rate) / 100.0
            client_rate_decimal = float(client_rate) / 100.0
            loan_margin_decimal = loan_markup / 100.0
            corporate_tax_decimal = float(corporate_tax) / 100.0
            inflation_rate_decimal = float(inflation_rate) / 100.0

            foreign_loan_rate = interest_rate_decimal + loan_margin_decimal
            interest_rate_diff = client_rate_decimal - foreign_loan_rate

            try:
                hedging_cost = self.hedging_calculator.compute_hedging_cost(currency_pair, horizon)
                hedging_type = "Forward Rate"
            except Exception as e:
                hedging_cost = inflation_rate_decimal
                hedging_type = "Log Inflation"

            pre_tax_arbitrage_profit = interest_rate_diff - hedging_cost
            post_tax_profit = pre_tax_arbitrage_profit * (1 - corporate_tax_decimal)
            risk_adjustment_factor = (101 - int(risk_rating))
            risk_adjusted_profit = post_tax_profit / risk_adjustment_factor

            opportunities.append({
                "country": country,
                "currency_code": currency_ticker,
                "interest_rate_diff": interest_rate_diff * 100,
                "annual_hedging_cost": hedging_cost * 100,
                "hedging_type": hedging_type,
                "pre_tax_arbitrage_profit": pre_tax_arbitrage_profit * 100,
                "post_tax_arbitrage_profit": post_tax_profit * 100,
                "risk_adjusted_profit": risk_adjusted_profit * 100,
                "risk_rating": risk_rating,
                "loan_margin_percentage": loan_margin_decimal * 100,
                "corporate_tax": corporate_tax,
                "inflation_rate": inflation_rate,
                "loan_interest_rate": interest_rate,
                "total_loan_rate": foreign_loan_rate * 100,
            })

        return sorted(opportunities, key=lambda x: x['risk_adjusted_profit'], reverse=True)

def test_arbitrage_analyzer():
    """Test function for standalone execution."""
    data_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/indicators/forex"
    forward_proxy_path = os.path.join(data_directory, "forward_proxy.csv")
    inflation_proxy_path = os.path.join(data_directory, "inflation_proxy.csv")
    analyzer = ArbitrageAnalyzer(data_directory, forward_proxy_path, inflation_proxy_path)
    client_rate_input = 12.0
    horizon_input = 6
    results = analyzer.analyze_opportunities(client_rate=client_rate_input, horizon=horizon_input, loan_markup=6.0)
    logging.info("Arbitrage analysis completed successfully.")
    results_df = pd.DataFrame(results)
    logging.info(f"Arbitrage Opportunities:\n{results_df.to_string()}")
    output_file_path = os.path.join(data_directory, "arbitrage_results.csv")
    results_df.to_csv(output_file_path, index=False)
    logging.info(f"Arbitrage opportunities exported to: {output_file_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    test_arbitrage_analyzer()