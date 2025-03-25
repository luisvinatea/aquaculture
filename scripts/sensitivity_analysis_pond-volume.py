from abc import ABC, abstractmethod
import json
import os
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import numpy as np

# Base class (unchanged)
class SaturationCalculator(ABC):
    def __init__(self, data_path):
        self.data_path = data_path
        self.load_data()
        
    def load_data(self):    
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                self.metadata = data["metadata"]
                self.matrix = data["data"]
                self.temp_step = self.metadata["temperature_range"]["step"]
                self.sal_step = self.metadata["salinity_range"]["step"]
        except FileNotFoundError:
            raise Exception(f"Data file not found at {self.data_path}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in data file")

    def get_o2_saturation(self, temperature, salinity):
        if not (0 <= temperature <= 40 and 0 <= salinity <= 40):
            raise ValueError("Temperature and salinity must be between 0 and 40")
        temp_idx = int(temperature / self.temp_step)
        sal_idx = int(salinity / self.sal_step)
        return self.matrix[temp_idx][sal_idx]

    @abstractmethod
    def calculate_sotr(self, temperature, salinity, *args, **kwargs):
        pass

# Implementation class (unchanged core functionality)
class ShrimpPondCalculator(SaturationCalculator):
    def __init__(self, data_path):
        super().__init__(data_path)
    
    def calculate_sotr(self, temperature, salinity, volume, efficiency=0.9):
        saturation = self.get_o2_saturation(temperature, salinity)
        return saturation * volume * efficiency

    def calculate_metrics(self, temperature, salinity, hp, volume, t10, t70, kwh_price):
        power_kw = hp * 0.746
        cs = self.get_o2_saturation(temperature, salinity)
        kla_t = 1.1 / ((t70 - t10) / 60)
        kla_20 = kla_t * (1.024 ** (20 - temperature))
        sotr = kla_20 * cs * volume * 0.001
        sae = sotr / power_kw
        cost_per_kg = kwh_price / sae
        
        return {
            "SOTR (kg O₂/h)": sotr,
            "SAE (kg O₂/kWh)": sae,
            "US$/kg O₂": cost_per_kg,
            "Power (kW)": power_kw
        }

    def get_ideal_volume(self, hp):
        """Return ideal pond volume based on HP"""
        if hp == 2:
            return 40
        elif hp == 3:
            return 70
        else:
            return hp * 25

# Interactive interface for hypothesis testing
def create_hypothesis_interface():
    calculator = ShrimpPondCalculator(
        "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
    )
    
    # Fixed parameters
    TEMPERATURE = 28
    SALINITY = 30
    T10 = 1  # 1 minute
    T70 = 8  # 8 minutes
    KWH_PRICE = 0.05  # Fixed at $0.05
    
    # Widgets
    model_type = widgets.Text(
        value='Beraqua Paddlewheel 3HP',
        description='Model Type:',
        layout={'width': '400px'}
    )
    
    horsepower = widgets.IntSlider(
        value=3, min=2, max=10, step=1, description='Horse Power:'
    )
    
    pond_volume = widgets.IntSlider(
        value=70, min=10, max=500, step=10, description='Pond Volume (m³):'
    )
    
    output = widgets.Output()
    
    def truncate_to_2_decimals(value):
        """Truncate float to 2 decimal places without rounding"""
        return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

    def plot_cost_comparison(calculated_cost, ideal_cost):
        """Plot a stacked bar chart comparing costs"""
        fig, ax = plt.subplots(figsize=(8, 6))
        categories = ['Calculated', 'Ideal']
        costs = [calculated_cost, ideal_cost]
        
        ax.bar(categories, costs, color=['#FF9999', '#66B2FF'])
        ax.set_ylabel('US$/kg O₂')
        ax.set_title('Cost per kg of Transferred Oxygen')
        for i, v in enumerate(costs):
            ax.text(i, v + 0.01, f"{v:.2f}", ha='center')
        plt.tight_layout()
        plt.show()

    def on_calculate_clicked(b):
        with output:
            clear_output()
            
            # Calculate metrics with user-specified volume
            calculated_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, horsepower.value, pond_volume.value, T10, T70, KWH_PRICE
            )
            
            # Calculate metrics with ideal volume
            ideal_volume = calculator.get_ideal_volume(horsepower.value)
            ideal_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, horsepower.value, ideal_volume, T10, T70, KWH_PRICE
            )
            
            # Truncate all float values to 2 decimal places
            calculated_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                                for k, v in calculated_metrics.items()}
            ideal_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                           for k, v in ideal_metrics.items()}
            
            # Calculate percentage variation in log scale
            log_variation = {}
            for key in calculated_metrics:
                if isinstance(calculated_metrics[key], float) and calculated_metrics[key] != 0:
                    diff = calculated_metrics[key] - ideal_metrics[key]
                    log_var = np.log10(abs(diff) + 1) * (1 if diff >= 0 else -1)
                    log_variation[key] = truncate_to_2_decimals(log_var)
            
            # Display results
            print(f"Model: {model_type.value}")
            print(f"Temperature: {TEMPERATURE} °C")
            print(f"Salinity: {SALINITY} ‰")
            print(f"Horse Power: {horsepower.value} HP")
            print(f"Selected Pond Volume: {pond_volume.value} m³")
            print(f"Ideal Pond Volume: {ideal_volume} m³")
            print(f"t₁₀: {T10} min")
            print(f"t₇₀: {T70} min")
            print(f"kWh Price: ${KWH_PRICE}")
            
            print("\nMetrics Comparison (Calculated vs Ideal):")
            for key in calculated_metrics:
                print(f"{key}: {calculated_metrics[key]} vs {ideal_metrics[key]} "
                      f"(Log % Variation: {log_variation.get(key, 'N/A')})")
            
            # Plot cost comparison
            plot_cost_comparison(calculated_metrics['US$/kg O₂'], ideal_metrics['US$/kg O₂'])
            
            # Export to file
            export_dir = "/home/luisvinatea/Dev/Repos/Aquaculture/reports/experiments"
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, 
                                  f"hypothesis_{model_type.value.replace(' ', '_')}_{horsepower.value}HP_{pond_volume.value}m3.txt")
            with open(filename, 'w') as f:
                f.write(f"Model: {model_type.value}\n")
                f.write(f"Temperature: {TEMPERATURE} °C\n")
                f.write(f"Salinity: {SALINITY} ‰\n")
                f.write(f"Horse Power: {horsepower.value} HP\n")
                f.write(f"Selected Pond Volume: {pond_volume.value} m³\n")
                f.write(f"Ideal Pond Volume: {ideal_volume} m³\n")
                f.write(f"t₁₀: {T10} min\n")
                f.write(f"t₇₀: {T70} min\n")
                f.write(f"kWh Price: ${KWH_PRICE}\n")
                f.write("\nMetrics Comparison (Calculated vs Ideal):\n")
                for key in calculated_metrics:
                    f.write(f"{key}: {calculated_metrics[key]} vs {ideal_metrics[key]} "
                            f"(Log % Variation: {log_variation.get(key, 'N/A')})\n")
            print(f"\nResults saved to {filename}")

    calculate_button = widgets.Button(description="Calculate")
    calculate_button.on_click(on_calculate_clicked)
    
    # Display interface
    display(
        widgets.VBox([
            model_type,
            horsepower,
            pond_volume,
            calculate_button,
            output
        ])
    )

if __name__ == "__main__":
    create_hypothesis_interface()