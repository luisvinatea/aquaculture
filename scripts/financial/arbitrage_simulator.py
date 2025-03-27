import pandas as pd
import os
from scripts.financial.arbitrage_calculator import ArbitrageAnalyzer

class CreditEvaluation:
    def __init__(self, aerator_price, aerator_quantity, client_rate, loan_rate, horizon, factoring_discount):
        self.aerator_price = aerator_price
        self.aerator_quantity = aerator_quantity
        self.client_rate = client_rate
        self.loan_rate = loan_rate
        self.horizon = horizon
        self.factoring_discount = factoring_discount
        self.initial_investment = (aerator_price * (1 - factoring_discount)) * aerator_quantity

    def calculate_cash_flows(self, client_rate, loan_rate):
        annual_amortization = self.initial_investment * (client_rate / (1 - (1 + client_rate) ** -self.horizon))
        return [-self.initial_investment] + [annual_amortization] * self.horizon

    def calculate_npv(self, cash_flows, reference_rate):
        return sum(f / ((1 + reference_rate) ** i) for i, f in enumerate(cash_flows))

    def calculate_pi(self, npv):
        return (npv + self.initial_investment) / abs(self.initial_investment)

# Data directories
data_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/indicators/financial/forex"
ecuador_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/shrimp_industry/ecuador"
simulator_directory = "/home/luisvinatea/Dev/Repos/Aquaculture/data/datasets/financial/arbitrage_simulator"

class Simulator:
    def __init__(self, data_directory, ecuador_directory):
        self.data_directory = data_directory
        self.ecuador_directory = ecuador_directory
        self.analyzer = ArbitrageAnalyzer(data_directory, ecuador_directory)
        self.analyzer.load_data()

    def analyze_opportunities(self, aerator_price, aerator_quantity, client_rate, horizon, factoring_discount, loan_markup):
        """
        Analyze arbitrage opportunities for the given parameters.

        Args:
            aerator_price (float): Price of the aerator.
            aerator_quantity (int): Quantity of aerators.
            client_rate (float): Annual interest rate charged to the client.
            horizon (int): Time horizon in years.
            factoring_discount (float): Factoring discount percentage.
            loan_markup (float): Loan markup percentage.

        Returns:
            tuple: A tuple containing the metrics DataFrame and the arbitrage opportunities DataFrame.
        """
        # Run arbitrage analysis
        client_rate_percentage = client_rate * 100
        arbitrage_results = self.analyzer.analyze_opportunities(client_rate=client_rate_percentage, horizon=horizon, loan_markup=loan_markup)

        # Financial Metrics Table
        evaluation = CreditEvaluation(aerator_price, aerator_quantity, client_rate, 0.05, horizon, factoring_discount)
        
        metrics_df = pd.DataFrame({
            'Metric': ['Aerator Price (PVP)', 'Aerator Quantity', 'Client Rate (Annual)', 'Horizon (Years)', 'Supplier Factoring Discount', 'Loan Markup (%)', 'Initial Investment'],
            'Value': [f"${aerator_price:.2f}", aerator_quantity, f"{client_rate * 100:.2f}%", horizon, f"{factoring_discount * 100:.2f}%", f"{loan_markup:.2f}%", f"${evaluation.initial_investment:.2f}"]
        })

        # Arbitrage Opportunities (Ranking)
        if isinstance(arbitrage_results, list) and arbitrage_results:
            sorted_results = sorted(arbitrage_results, key=lambda x: x['risk_adjusted_profit'], reverse=True)[:20]

            arbitrage_data = []
            for res in sorted_results:
                total_loan_rate = res['total_loan_rate'] / 100.0  # Base + markup
                eval_country = CreditEvaluation(aerator_price, aerator_quantity, client_rate, total_loan_rate, horizon, factoring_discount)
                cash_flows_country = eval_country.calculate_cash_flows(client_rate, total_loan_rate)
                npv_country = eval_country.calculate_npv(cash_flows_country, total_loan_rate)
                pi_country = eval_country.calculate_pi(npv_country)
                arbitrage_data.append({
                    'Country': res['country'],
                    'Adjusted Profitability (%)': res['risk_adjusted_profit'],
                    'Base Loan Rate (%)': res['loan_interest_rate'],
                    'Total Loan Rate (%)': res['total_loan_rate'],  # Show base + markup
                    'Annualized Coverage Cost (%)': res['annual_hedging_cost'],
                    'Coverage Cost Type': res['hedging_type'],
                    'NPV': npv_country,
                    'PI': pi_country,
                    'Interest Rate Differential (%)': res['interest_rate_diff'],
                    'Pre-Tax Arbitrage Profit (%)': res['pre_tax_arbitrage_profit'],
                    'Post-Tax Arbitrage Profit (%)': res['post_tax_arbitrage_profit'],
                    'Risk Rating (te)': res['risk_rating'],
                    'Loan Markup (%)': loan_markup,
                    'Corporate Tax (%)': res['corporate_tax'],
                    'Inflation Rate (%)': res['inflation_rate'],
                    'Spot Exchange Rate': res['spot_exchange_rate'],
                    'Forward Exchange Rate': res['forward_exchange_rate']
                })

            arbitrage_df = pd.DataFrame(arbitrage_data)
            arbitrage_df['NPV'] = arbitrage_df['NPV'].apply(lambda x: f"${x:.2f}")
            arbitrage_df['PI'] = arbitrage_df['PI'].apply(lambda x: f"{x:.4f}")
            arbitrage_df['Spot Exchange Rate'] = arbitrage_df['Spot Exchange Rate'].apply(lambda x: f"{x:.4f}")
            arbitrage_df['Forward Exchange Rate'] = arbitrage_df['Forward Exchange Rate'].apply(lambda x: f"{x:.4f}")
        else:
            arbitrage_df = pd.DataFrame()  # Empty DataFrame if no results

        return metrics_df, arbitrage_df

    def save_results(self, metrics_df, arbitrage_df, aerator_price, aerator_quantity, client_rate, horizon, factoring_discount, loan_markup):
        """
        Save the results to CSV files in a folder.

        Args:
            metrics_df (pd.DataFrame): Metrics DataFrame.
            arbitrage_df (pd.DataFrame): Arbitrage opportunities DataFrame.
            aerator_price (float): Price of the aerator.
            aerator_quantity (int): Quantity of aerators.
            client_rate (float): Annual interest rate charged to the client.
            horizon (int): Time horizon in years.
            factoring_discount (float): Factoring discount percentage.
            loan_markup (float): Loan markup percentage.
        """
        # Construct folder name
        initial_investment = (aerator_price * (1 - factoring_discount)) * aerator_quantity
        folder_name = f"simulator_results_{aerator_price}_{aerator_quantity}_{initial_investment}_{loan_markup}_{client_rate * 100}_{factoring_discount * 100}_{horizon}"
        folder_path = os.path.join(simulator_directory, folder_name)
        
        # Create the folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        
        # Save the metrics table
        metrics_filepath = os.path.join(folder_path, "metrics.csv")
        metrics_df.to_csv(metrics_filepath, index=False)
        
        # Save the arbitrage opportunities table
        arbitrage_filepath = os.path.join(folder_path, "arbitrage_opportunities.csv")
        arbitrage_df.to_csv(arbitrage_filepath, index=False)
        
        print(f"Results saved to folder: {folder_path}")

def setup_simulator():
    """
    Initialize and return a Simulator instance.

    Returns:
        Simulator: An instance of the Simulator class.
    """
    return Simulator(data_directory, ecuador_directory)

# Example usage
if __name__ == "__main__":
    simulator = setup_simulator()
    
    # Example parameters
    aerator_price = 1200
    aerator_quantity = 100
    client_rate = 0.13
    horizon = 6
    factoring_discount = 0.10
    loan_markup = 4.0

    # Analyze opportunities
    metrics_df, arbitrage_df = simulator.analyze_opportunities(aerator_price, aerator_quantity, client_rate, horizon, factoring_discount, loan_markup)

    # Print results
    print("Metrics:")
    print(metrics_df)
    print("\nArbitrage Opportunities:")
    print(arbitrage_df)

    # Save results
    simulator.save_results(metrics_df, arbitrage_df, aerator_price, aerator_quantity, client_rate, horizon, factoring_discount, loan_markup)