import os
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import numpy as np
from sae_sotr_calculator import ShrimpPondCalculator

def truncate_to_2_decimals(value):
    """Truncate float to 2 decimal places without rounding"""
    return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

def create_hypothesis_interface():
    calculator = ShrimpPondCalculator(
        "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
    )
    
    # Fixed parameters
    TEMPERATURE = 28
    SALINITY = 30
    T10 = 1
    T70 = 8
    KWH_PRICE = 0.05
    
    # Widgets
    model_type = widgets.Text(value='Beraqua Paddlewheel 3HP', description='Model Type:', layout={'width': '400px'})
    horsepower = widgets.IntSlider(value=3, min=2, max=10, step=1, description='Horse Power:')
    pond_volume = widgets.IntSlider(value=70, min=10, max=500, step=10, description='Pond Volume (m³):')
    output = widgets.Output()
    
    def plot_cost_comparison(calculated_cost, ideal_cost):
        fig, ax = plt.subplots(figsize=(8, 6))
        categories = ['Selected HP', 'Ideal HP']
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
            calculated_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, horsepower.value, pond_volume.value, T10, T70, KWH_PRICE
            )
            ideal_hp = calculator.get_ideal_hp(pond_volume.value)
            ideal_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, ideal_hp, pond_volume.value, T10, T70, KWH_PRICE
            )
            ideal_volume = calculator.get_ideal_volume(horsepower.value)
            
            calculated_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                                for k, v in calculated_metrics.items()}
            ideal_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                           for k, v in ideal_metrics.items()}
            
            log_variation = {}
            for key in calculated_metrics:
                if isinstance(calculated_metrics[key], float) and calculated_metrics[key] != 0:
                    diff = calculated_metrics[key] - ideal_metrics[key]
                    log_var = np.log10(abs(diff) + 1) * (1 if diff >= 0 else -1)
                    log_variation[key] = truncate_to_2_decimals(log_var)
            
            print(f"Model: {model_type.value}")
            print(f"Temperature: {TEMPERATURE} °C")
            print(f"Salinity: {SALINITY} ‰")
            print(f"Selected Horse Power: {horsepower.value} HP")
            print(f"Ideal Horse Power for {pond_volume.value} m³: {ideal_hp} HP")
            print(f"Selected Pond Volume: {pond_volume.value} m³")
            print(f"Ideal Pond Volume for {horsepower.value} HP: {ideal_volume} m³")
            print(f"t₁₀: {T10} min")
            print(f"t₇₀: {T70} min")
            print(f"kWh Price: ${KWH_PRICE}")
            print("\nMetrics Comparison (Selected HP vs Ideal HP):")
            for key in calculated_metrics:
                print(f"{key}: {calculated_metrics[key]} vs {ideal_metrics[key]} "
                      f"(Log % Variation: {log_variation.get(key, 'N/A')})")
            
            plot_cost_comparison(calculated_metrics['US$/kg O₂'], ideal_metrics['US$/kg O₂'])
            
            export_dir = "/home/luisvinatea/Dev/Repos/Aquaculture/reports/experiments"
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, 
                                  f"hypothesis_{model_type.value.replace(' ', '_')}_{horsepower.value}HP_{pond_volume.value}m3.txt")
            with open(filename, 'w') as f:
                f.write(f"Model: {model_type.value}\n")
                f.write(f"Temperature: {TEMPERATURE} °C\n")
                f.write(f"Salinity: {SALINITY} ‰\n")
                f.write(f"Selected Horse Power: {horsepower.value} HP\n")
                f.write(f"Ideal Horse Power for {pond_volume.value} m³: {ideal_hp} HP\n")
                f.write(f"Selected Pond Volume: {pond_volume.value} m³\n")
                f.write(f"Ideal Pond Volume for {horsepower.value} HP: {ideal_volume} m³\n")
                f.write(f"t₁₀: {T10} min\n")
                f.write(f"t₇₀: {T70} min\n")
                f.write(f"kWh Price: ${KWH_PRICE}\n")
                f.write("\nMetrics Comparison (Selected HP vs Ideal HP):\n")
                for key in calculated_metrics:
                    f.write(f"{key}: {calculated_metrics[key]} vs {ideal_metrics[key]} "
                            f"(Log % Variation: {log_variation.get(key, 'N/A')})\n")
            print(f"\nResults saved to {filename}")

    calculate_button = widgets.Button(description="Calculate")
    calculate_button.on_click(on_calculate_clicked)
    
    display(widgets.VBox([model_type, horsepower, pond_volume, calculate_button, output]))

if __name__ == "__main__":
    create_hypothesis_interface()