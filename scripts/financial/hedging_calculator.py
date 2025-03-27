import pandas as pd
import os
import numpy as np

# US inflation rate (constant, as defined previously)
us_inflation_rate = 3.0

class HedgingCostCalculator:
    def __init__(self, inflation_proxy_path, forward_proxy_path, verbose=True): # Add verbose parameter, default True
        """
        Initialize the HedgingCostCalculator with paths to spot, forward proxy, and inflation proxy CSV files.
        """
        self.inflation_proxy_path = inflation_proxy_path
        self.forward_proxy_path = forward_proxy_path
        self.forward_proxy_data = None
        self.inflation_proxy_data = None
        self.verbose = verbose # Store verbose setting

        # Load data on initialization
        self._load_data()

    def _load_data(self):
        """
        Load spot, forward proxy, and inflation proxy data from the provided CSV files.
        """
        try:
            self.forward_proxy_data = pd.read_csv(self.forward_proxy_path)
            self.inflation_proxy_data = pd.read_csv(self.inflation_proxy_path)
            # Print first few rows to inspect data loading - Inflation Proxy, Conditionally
            if self.verbose: # Only print if verbose is True
                print("Inflation Proxy Data sample:")
                print(self.inflation_proxy_data.head())
            # Print first few rows to inspect data loading - Forward Proxy, Conditionally
            if self.verbose: # Only print if verbose is True
                print("Forward Proxy Data sample:")
                print(self.forward_proxy_data.head())
        except Exception as e:
            raise Exception(f"Error loading data: {e}")

    def compute_hedging_cost(self, currency_pair, time_horizon):
        """
        Compute the hedging cost for a given currency pair and time horizon.
        Uses forward proxy data if available, otherwise uses log inflation differential proxy.

        :param currency_pair: The currency pair in the format 'usd_xxx' (e.g., 'usd_eur').
        :param time_horizon: The time horizon in years (e.g., 1 for 1 year).
        :return: The hedging cost as a float.
        """
        if self.inflation_proxy_data is None or self.forward_proxy_data is None or self.inflation_proxy_data is None:
            raise Exception("Data not loaded. Please check the CSV file paths.")

        if currency_pair == "usd_usd":
            return 0.0  # Hedging cost for USD/USD is 0

        # Find the spot rate for the given currency pair from inflation proxy as spot data is there for all currencies
        spot_rate_series = self.inflation_proxy_data.loc[self.inflation_proxy_data['currency_pair'] == currency_pair, 'spot_price']

        if not spot_rate_series.empty:
            spot_rate = spot_rate_series.iloc[0] # Get the first value if series is not empty
        else:
            spot_rate = None # Spot rate not found


        # Try to find forward proxy rate
        forward_rate_series = self.forward_proxy_data.loc[self.forward_proxy_data['currency_pair'] == currency_pair, 'future_price']
        spot_hedge_series = self.forward_proxy_data.loc[self.forward_proxy_data['currency_pair'] == currency_pair, 'spot_price']

        if not forward_rate_series.empty:
            # Forward proxy data is available, compute hedging cost using forward proxy
            forward_rate = forward_rate_series.iloc[0]
            spot_rate_hedge = spot_hedge_series.iloc[0] # Use spot price from hedge file, not inflation proxy
            if spot_rate_hedge is not None:
                hedging_cost_forward_proxy = (forward_rate / spot_rate_hedge) ** (1 / time_horizon) - 1 # Corrected formula: forward_rate / spot_rate
                return hedging_cost_forward_proxy
            else:
                raise ValueError(f"Spot data needed but not found in forward proxy file for currency pair: {currency_pair} to compute forward proxy based cost.")

        else:
            # Forward proxy data is not available, use inflation proxy (LOG DIFFERENTIAL)
            inflation_differential_series = self.inflation_proxy_data.loc[self.inflation_proxy_data['currency_pair'] == currency_pair, 'inflation_differential']
            if not inflation_differential_series.empty:
                inflation_differential = inflation_differential_series.iloc[0]
                foreign_inflation_rate = inflation_differential + us_inflation_rate # Calculate foreign inflation
                hedging_cost_inflation_proxy = np.log1p(foreign_inflation_rate / 100.0) - np.log1p(us_inflation_rate / 100.0) # Log differential
                return hedging_cost_inflation_proxy
            else:
                raise ValueError(f"No hedging data (forward proxy or inflation proxy) found for currency pair: {currency_pair}")

# Example usage (for testing)
if __name__ == "__main__":
    # Paths to the CSV files
    forward_proxy_path = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/indicators/financial/forex/forward_proxy.csv" # Renamed to forward_proxy_path
    inflation_proxy_path = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/indicators/financial/forex/inflation_proxy.csv" # Path to the inflation proxy file

    # Initialize the calculator
    calculator = HedgingCostCalculator(inflation_proxy_path, forward_proxy_path) # verbose defaults to True

    # Example 1: Compute hedging cost for USD/JPY (should use forward proxy if available)
    currency_pair_forward_proxy = "usd_jpy"
    time_horizon = 1  # in year
    try:
        hedging_cost_forward_proxy = calculator.compute_hedging_cost(currency_pair_forward_proxy, time_horizon)
        print(f"Hedging cost for {currency_pair_forward_proxy} over {time_horizon} year(s) (using forward proxy): {hedging_cost_forward_proxy:.6f}")
    except Exception as e:
        print(f"Error for {currency_pair_forward_proxy}: {e}")

    # Example 2: Compute hedging cost for USD/SYP (should use inflation proxy as forward proxy likely unavailable)
    currency_pair_inflation_proxy = "usd_syp"
    time_horizon = 1  # in year
    try:
        hedging_cost_inflation_proxy = calculator.compute_hedging_cost(currency_pair_inflation_proxy, time_horizon)
        print(f"Hedging cost for {currency_pair_inflation_proxy} over {time_horizon} year(s) (using log inflation proxy): {hedging_cost_inflation_proxy:.6f}")
    except Exception as e:
        print(f"Error for {currency_pair_inflation_proxy}: {e}")

    # Example 3: Example with longer time horizon for forward proxy based currency
    currency_pair_forward_proxy_long_term = "usd_chf" # Example currency with forward proxy
    time_horizon_long_term = 6  # in years
    try:
        hedging_cost_forward_proxy_long_term = calculator.compute_hedging_cost(currency_pair_forward_proxy_long_term, time_horizon_long_term)
        print(f"Hedging cost for {currency_pair_forward_proxy_long_term} over {time_horizon_long_term} year(s) (using forward proxy): {hedging_cost_forward_proxy_long_term:.6f}")
    except Exception as e:
        print(f"Error for {currency_pair_forward_proxy_long_term}: {e}")

    # Example 4: Example with currency that is USD_USD
    currency_pair_usd_usd = "usd_usd" # Example currency usd_usd
    time_horizon_usd_usd = 1
    try:
        hedging_cost_usd_usd = calculator.compute_hedging_cost(currency_pair_usd_usd, time_horizon_usd_usd)
        print(f"Hedging cost for {currency_pair_usd_usd} over {time_horizon_usd_usd} year(s): {hedging_cost_usd_usd:.6f}")
    except Exception as e:
        print(f"Error for {currency_pair_usd_usd}: {e}")

    # Example 5: Example with currency that might have neither (for error handling - adapt as needed for your data)
    currency_pair_no_data = "usd_xxx" # Example currency with no data (or adjust to a real one without data in your files)
    time_horizon_no_data = 1
    try:
        hedging_cost_no_data = calculator.compute_hedging_cost(currency_pair_no_data, time_horizon_no_data)
        hedging_cost_no_data
        print(f"Hedging cost for {currency_pair_no_data} over {time_horizon_no_data} year(s): {hedging_cost_no_data:.6f}")
    except Exception as e:
        print(f"Error for {currency_pair_no_data}: {e}")