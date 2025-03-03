import yfinance as yf
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Remove duplicates from the currency list
SPOT_CURRENCIES = list(set([
    'AFN','ALL','DZD','EUR','AOA','ARS','AMD','AWG','AUD','AZN','BSD','BHD','BDT','BBD','BYN','BZD','XOF',
    'BMD','BTN','BOB','BAM','BWP','BRL','BND','BGN','XAF','CAD','CVE','KYD','CLP','CNY','COP','KMF','CRC',
    'CZK','DKK','XCD','DOP','EGP','ETB','FJD','GMD','GEL','GHS','GTQ','GNF','GYD','HTG','HNL','HKD','HUF',
    'ISK','INR','IDR','IQD','GBP','ILS','JMD','JPY','JOD','KZT','KES','KWD','KGS','LAK','LBP','LSL','LYD',
    'CHF','MOP','MKD','MGA','MWK','MYR','MVR','MRU','MUR','MXN','MDL','MNT','MAD','MZN','MMK','NAD','NPR',
    'NZD','NIO','NGN','NOK','OMR','PKR','PAB','PGK','PYG','PEN','PHP','PLN','USD','QAR','RON','RUB','RWF',
    'WST','SAR','RSD','SCR','SLL','SGD','SBD','ZAR','KRW','LKR','SDG','SRD','SZL','SEK','SYP','TWD','TZS',
    'THB','TOP','TTD','TND','TRY','UGX','UAH','AED','UYU','UZS','VUV','VES','VND','ZMW','ZWG'
]))

# Portable file paths
data_dir = "/home/luisvinatea/Dev/Repos/aquaculture/beraqua/notebooks/datasets/indicators/forex"
SPOT_CSV_PATH = os.path.join(data_dir, "exchange_rate_spot.csv")
FUTURES_CSV_PATH = os.path.join(data_dir, "exchange_rate_futures.csv")
ALL_SPOT_CSV_PATH = os.path.join(data_dir, "all_spot_exchange_rates.csv")
FORWARD_PROXY_CSV_PATH = os.path.join(data_dir, "forward_proxy.csv")

# Fetch spot data
def fetch_spot_data():
    data = []
    for currency in SPOT_CURRENCIES:
        ticker_symbol = f'{currency}=X'
        ticker = yf.Ticker(ticker_symbol)
        try:
            hist = ticker.history(period='1d')
            if not hist.empty:
                rate = hist['Close'].iloc[-1]
                pair_name = f'usd_{currency.lower()}'
                data.append({'currency_pair': pair_name, 'spot_price': rate})
            else:
                logging.warning(f"No data found for {ticker_symbol}")
        except Exception as e:
            logging.error(f"Error fetching spot data for {ticker_symbol}: {e}")
    return pd.DataFrame(data)

# Fetch futures data and invert the quotation
def fetch_futures_data():
    data = []
    FUTURES_MAPPING = {
        'EUR': '6E=F', 'AUD': '6A=F', 'BRL': '6L=F', 'CAD': '6C=F',
        'CNY': '6Y=F', 'HUF': '6H=F', 'INR': '6I=F', 'GBP': '6B=F',
        'JPY': '6J=F', 'CHF': '6S=F', 'MXN': '6M=F', 'NZD': '6N=F',
        'NOK': 'NOK=F', 'PLN': 'PLN=F', 'RUB': '6R=F', 'ZAR': '6Z=F',
        'KRW': 'KRW=F', 'SEK': 'SEK=F', 'TRY': 'TRY=F'
    }
    for currency, futures_symbol in FUTURES_MAPPING.items():
        ticker = yf.Ticker(futures_symbol)
        try:
            hist = ticker.history(period='1d')
            if not hist.empty:
                rate = hist['Close'].iloc[-1]
                # Invert the futures price to match the spot format
                inverted_rate = 1 / rate
                pair_name = f'usd_{currency.lower()}'
                data.append({'currency_pair': pair_name, 'future_price': inverted_rate})
            else:
                logging.warning(f"No data found for {futures_symbol}")
        except Exception as e:
            logging.error(f"Error fetching futures data for {futures_symbol}: {e}")
    return pd.DataFrame(data)

# Save data without backup
def save_data(df, file_path, columns):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False, columns=columns, float_format='%.6f')
    logging.info(f"Data saved: {file_path}")

def main():
    # Fetch data from both markets
    spot_df = fetch_spot_data()
    futures_df = fetch_futures_data()

    # Merge spot and futures data on 'currency_pair'
    merged_df = pd.merge(spot_df, futures_df, on='currency_pair', how='left')

    # Save the merged data to forward_proxy.csv
    save_data(merged_df, FORWARD_PROXY_CSV_PATH, ['currency_pair', 'spot_price', 'future_price'])

    # Identify non-matching currency pairs
    non_matching_pairs = set(spot_df['currency_pair']) - set(futures_df['currency_pair'])
    non_matching_df = spot_df[spot_df['currency_pair'].isin(non_matching_pairs)]

    # Save non-matching pairs to a separate CSV file
    save_data(non_matching_df, ALL_SPOT_CSV_PATH, ['currency_pair', 'spot_price'])

if __name__ == '__main__':
    main()