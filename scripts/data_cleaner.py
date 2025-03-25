import os
import pandas as pd
import json
import geopandas

class CSVProcessor:
    def __init__(self, directory_path, currency_tickers_path, shapefile_path):
        self.directory_path = directory_path
        self.currency_tickers_path = currency_tickers_path
        self.shapefile_path = shapefile_path
        self.country_metadata = {}
        self.eurozone_interest_rate = None
        self._load_eurozone_interest_rate()

    def process_files(self):
        """Process all CSV files in the specified directory."""
        for file_name in os.listdir(self.directory_path):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.directory_path, file_name)
                self._process_file(file_path)
        self._apply_eurozone_interest_rate()
        self._save_country_metadata_summary()
        self._process_shapefile()

    def _process_file(self, file_path):
        try:
            df = pd.read_csv(file_path)
            cleaned_df = self._clean_dataframe(df)
            self._extract_country_metadata(cleaned_df)
            cleaned_df.to_csv(file_path, index=False)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    def _clean_dataframe(self, df):
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].str.strip()
        
        column_type_mapping = {
            'country': 'object',
            'currency_ticker': 'object',
            'currency_pair': 'object',
            'spot_price': 'float64',
            'future_price': 'float64',
            'interest_yield': 'float64',
            'deposit_rate': 'float64',
            'inflation_rate': 'float64',
            'interbank_rate': 'float64',
            'corporate_tax': 'float64',
            'interest_rate': 'float64',
            'te': 'int64',
        }

        for column, dtype in column_type_mapping.items():
            if column in df.columns:
                try:
                    df[column] = df[column].astype(dtype)
                except Exception:
                    pass
        return df

    def _extract_country_metadata(self, df):
        if 'country' in df.columns:
            for _, row in df.iterrows():
                country_name = row['country']
                row_dict = row.to_dict()
                # Exclude the 'country' key from the metadata
                country_data = {k: v for k, v in row_dict.items() if k != 'country'}
                # Update the country_metadata dictionary
                if country_name not in self.country_metadata:
                    self.country_metadata[country_name] = {}
                self.country_metadata[country_name].update(country_data)

    def _load_eurozone_interest_rate(self):
        interest_rate_file = os.path.join(self.directory_path, "interest_rate.csv")
        try:
            df_interest_rate = pd.read_csv(interest_rate_file)
            eurozone_row = df_interest_rate[df_interest_rate['country'] == 'euro_area']
            if not eurozone_row.empty:
                self.eurozone_interest_rate = eurozone_row['interest_rate'].iloc[0]
        except (FileNotFoundError, Exception) as e:
            print(f"Error loading eurozone interest rate: {e}")

    def _apply_eurozone_interest_rate(self):
        if self.eurozone_interest_rate is not None:
            for country_name, data in self.country_metadata.items():
                if data.get('currency_ticker') == 'eur':
                    self.country_metadata[country_name]['interest_rate'] = self.eurozone_interest_rate

    def _save_country_metadata_summary(self):
        summary_file_path = os.path.join(self.directory_path, "country_metadata_summary.json")
        try:
            with open(summary_file_path, 'w') as f:
                json.dump(self.country_metadata, f, indent=4)
            print(f"Country metadata saved to {summary_file_path}")
        except Exception as e:
            print(f"Failed to save country metadata: {e}")

    def _process_shapefile(self):
        try:
            world = geopandas.read_file(self.shapefile_path)
            
            # Save as GeoPackage (recommended)
            gpkg_path = self.shapefile_path.replace('.shp', '.gpkg')
            world.to_file(gpkg_path, driver='GPKG')
            
            # Optional: Save as GeoJSON
            geojson_path = self.shapefile_path.replace('.shp', '.geojson')
            world.to_file(geojson_path, driver='GeoJSON')
            
        except Exception as e:
            print(f"Error processing shapefile: {e}")

if __name__ == "__main__":
    directory_to_process = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/indicators/forex"
    currency_tickers_path = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/indicators/forex/currency_tickers.csv"
    shapefile_path = "/home/luisvinatea/Dev/Repos/Aquaculture/beraqua/data/raw/shapefiles/ne_110m_admin_0_countries.shp"
    
    processor = CSVProcessor(directory_to_process, currency_tickers_path, shapefile_path)
    processor.process_files()