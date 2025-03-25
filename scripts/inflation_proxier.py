import pandas as pd
import os

# Define file paths based on user's provided paths
base_dir = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/indicators/financial/forex/"
spot_exchange_rates_file = os.path.join(base_dir, "all_spot_exchange_rates.csv")
currency_tickers_file = os.path.join(base_dir, "currency_tickers.csv")
inflation_rates_file = os.path.join(base_dir, "inflation_rates.csv")
output_file = os.path.join(base_dir, "inflation_proxy.csv")

# US inflation rate
us_inflation_rate = 3.0

def compute_inflation_differentials(spot_exchange_rates_path, currency_tickers_path, inflation_rates_path, output_path, us_inflation):
    """
    Computes the inflation rate differential for countries in the spot exchange rates dataset.

    Args:
        spot_exchange_rates_path (str): Path to the CSV file with spot exchange rates.
        currency_tickers_path (str): Path to the CSV file with currency tickers.
        inflation_rates_path (str): Path to the CSV file with inflation rates.
        output_path (str): Path to save the output CSV file.
        us_inflation (float): US inflation rate.
    """

    # Load the datasets
    try:
        spot_rates_df = pd.read_csv(spot_exchange_rates_path)
        currency_tickers_df = pd.read_csv(currency_tickers_path)
        inflation_df = pd.read_csv(inflation_rates_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Error: One or more input files not found. {e}")

    # 1. Extract currency tickers from 'currency_pair' column in spot_rates_df
    spot_rates_df['currency_ticker'] = spot_rates_df['currency_pair'].str.split('_').str[1]

    # 2. Merge spot_rates_df with currency_tickers_df to get country names
    merged_df = pd.merge(spot_rates_df, currency_tickers_df, on='currency_ticker', how='left')

    # 3. Merge with inflation_df to get inflation rates
    merged_df = pd.merge(merged_df, inflation_df, on='country', how='left')

    # 4. Calculate inflation differential
    merged_df['inflation_differential'] = merged_df['inflation_rate'] - us_inflation

    # 5. Select the desired columns and write to output_path
    output_df = merged_df[['currency_pair', 'spot_price', 'inflation_differential']]

    try:
        output_df.to_csv(output_path, index=False)
        print(f"Successfully created inflation differential proxy at: {output_path}")
    except Exception as e:
        raise Exception(f"Error writing to output file: {e}")


if __name__ == "__main__":
    try:
        compute_inflation_differentials(
            spot_exchange_rates_file,
            currency_tickers_file,
            inflation_rates_file,
            output_file,
            us_inflation_rate
        )
    except FileNotFoundError as e:
        print(f"File Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")