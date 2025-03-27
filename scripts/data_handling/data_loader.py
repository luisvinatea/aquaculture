import os
import pandas as pd
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ArbitrageAnalyzer:
    def __init__(self, data_directory, ecuador_directory):
        self.data_directory = data_directory
        self.ecuador_directory = ecuador_directory
        self.country_metadata = None
        self.exchange_rates_df = None
        self.forward_rates_df = None
        self.ecuador_credit_rates_df = None
        self.ecuador_shrimp_prices_df = None
        self.ecuador_default_rates_df = None
        self.ecuador_shrimp_exporters_df = None

    def load_data(self):
        try:
            metadata_path = os.path.join(self.data_directory, "country_metadata_summary.json")
            with open(metadata_path, 'r') as f:
                self.country_metadata = json.load(f)
            logging.info("Country metadata loaded successfully.")

            self.exchange_rates_df = self._load_csv("exchange_rate_spot.csv", self.data_directory)
            self.forward_rates_df = self._load_csv("exchange_rate_futures.csv", self.data_directory)
            self.ecuador_credit_rates_df = self._load_csv("ecuador_credit_segments.csv", self.ecuador_directory)
            self.ecuador_shrimp_prices_df = self._load_csv("shrimp_prices.csv", self.ecuador_directory)
            self.ecuador_default_rates_df = self._load_csv("ecuador_default_rates_2018-2019.csv", self.ecuador_directory)
            self.ecuador_shrimp_exporters_df = self._load_csv("shrimp_exporters.csv", self.ecuador_directory)

            logging.info("All data successfully loaded.")
        except Exception as e:
            logging.error(f"Data loading failed. Check file paths and formats. Error: {e}")
            raise

    def _load_csv(self, file_name, directory):
        file_path = os.path.join(directory, file_name)
        try:
            df = pd.read_csv(file_path)
            logging.info(f"File loaded: {file_path}")
            return df
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return None
        except pd.errors.ParserError as e:
            logging.error(f"CSV parsing error {file_path}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error loading {file_path}: {e}")
            return None

if __name__ == "__main__":
    data_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/indicators/financial/forex"
    ecuador_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/shrimp_industry/ecuador"
    
    analyzer = ArbitrageAnalyzer(data_directory, ecuador_directory)
    analyzer.load_data()
