from abc import ABC, abstractmethod
import json
import os
import ipywidgets as widgets
from IPython.display import display, clear_output

class SaturationCalculator(ABC):
    def __init__(self, data_path):
        """Initialize with path to JSON data file"""
        self.data_path = data_path
        self.load_data()
        
    def load_data(self):
        """Load the saturation data from JSON"""
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
        """Get O2 saturation value for given temperature and salinity"""
        if not (0 <= temperature <= 40 and 0 <= salinity <= 40):
            raise ValueError("Temperature and salinity must be between 0 and 40")
        
        # Convert to matrix indices
        temp_idx = int(temperature / self.temp_step)
        sal_idx = int(salinity / self.sal_step)
        
        return self.matrix[temp_idx][sal_idx]

    @abstractmethod
    def calculate_sotr(self, temperature, salinity, *args, **kwargs):
        """Abstract method to calculate Standard Oxygen Transfer Rate"""
        pass

class ShrimpPondCalculator(SaturationCalculator):
    def __init__(self, data_path):
        super().__init__(data_path)
    
    def calculate_sotr(self, temperature, salinity, volume, efficiency=0.9):
        """Calculate SOTR for shrimp pond"""
        saturation = self.get_o2_saturation(temperature, salinity)
        return saturation * volume * efficiency

    def calculate_metrics(self, temperature, salinity, hp, t10, t70, kwh_price):
        """Calculate all required metrics"""
        # Calculate pond volume based on HP
        if hp == 2:
            volume = 40
        elif hp == 3:
            volume = 70
        else:
            volume = hp * 25  # General rule: 25 m³ per HP for others
        
        # Power in kW (1 HP = 0.746 kW)
        power_kw = hp * 0.746
        
        # Get Cs (saturation concentration)
        cs = self.get_o2_saturation(temperature, salinity)
        
        # Calculate KlaT (h⁻¹)
        kla_t = 1.1 / ((t70 - t10) / 60)
        
        # Calculate Kla20 (h⁻¹)
        kla_20 = kla_t * (1.024 ** (20 - temperature))
        
        # Calculate SOTR (kg O₂/h)
        sotr = kla_20 * cs * volume * 0.001  # Convert g to kg
        
        # Calculate SAE (kg O₂/kWh)
        sae = sotr / power_kw
        
        # Calculate Cost per kg O₂ (US$/kg O₂)
        cost_per_kg = kwh_price / sae
        
        return {
            "Pond Volume (m³)": volume,
            "Cs (kg/m³)": cs,
            "KlaT (h⁻¹)": kla_t,
            "Kla20 (h⁻¹)": kla_20,
            "SOTR (kg O₂/h)": sotr,
            "SAE (kg O₂/kWh)": sae,
            "US$/kg O₂": cost_per_kg,
            "Power (kW)": power_kw
        }

# Interactive interface
def create_interface():
    calculator = ShrimpPondCalculator(
        "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
    )
    
    # Widgets
    model_type = widgets.Text(
        value='Beraqua Paddlewheel 3HP',
        description='Model Type:',
        layout={'width': '400px'}
    )
    
    temperature = widgets.FloatSlider(
        value=25.0, min=0, max=40, step=1, description='Temperature (°C):'
    )
    
    salinity = widgets.FloatSlider(
        value=15.0, min=0, max=40, step=5, description='Salinity (‰):'
    )
    
    horsepower = widgets.IntSlider(
        value=3, min=2, max=10, step=1, description='Horse Power:'
    )
    
    # t10 input: minutes and seconds
    t10_min = widgets.IntText(value=5, description='t₁₀ (min):', layout={'width': '150px'})
    t10_sec = widgets.IntText(value=0, min=0, max=59, description='sec:', layout={'width': '150px'})
    
    # t70 input: minutes and seconds
    t70_min = widgets.IntText(value=20, description='t₇₀ (min):', layout={'width': '150px'})
    t70_sec = widgets.IntText(value=0, min=0, max=59, description='sec:', layout={'width': '150px'})
    
    kwh_price = widgets.FloatSlider(
        value=0.05, min=0.01, max=0.5, step=0.01, description='Price kWh (US$):'
    )
    
    output = widgets.Output()
    
    def convert_to_minutes(minutes, seconds):
        """Convert minutes and seconds to decimal minutes"""
        return minutes + (seconds / 60.0)
    
    def truncate_to_2_decimals(value):
        """Truncate float to 2 decimal places without rounding"""
        return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

    def on_calculate_clicked(b):
        with output:
            clear_output()
            # Convert t10 and t70 to decimal minutes
            t10 = convert_to_minutes(t10_min.value, t10_sec.value)
            t70 = convert_to_minutes(t70_min.value, t70_sec.value)
            
            results = calculator.calculate_metrics(
                temperature.value,
                salinity.value,
                horsepower.value,
                t10,
                t70,
                kwh_price.value
            )
            
            # Truncate all float results to 2 decimal places
            truncated_results = {key: truncate_to_2_decimals(value) if isinstance(value, float) else value 
                               for key, value in results.items()}
            truncated_t10 = truncate_to_2_decimals(t10)
            truncated_t70 = truncate_to_2_decimals(t70)
            truncated_kwh_price = truncate_to_2_decimals(kwh_price.value)
            
            # Display results
            print(f"Model: {model_type.value}")
            print(f"Temperature: {temperature.value} °C")
            print(f"Salinity: {salinity.value} ‰")
            print(f"Horse Power: {horsepower.value} HP")
            print(f"t₁₀: {t10_min.value} min {t10_sec.value} sec ({truncated_t10} minutes)")
            print(f"t₇₀: {t70_min.value} min {t70_sec.value} sec ({truncated_t70} minutes)")
            print(f"kWh Price: ${truncated_kwh_price}")
            print("\nCalculated Metrics:")
            for key, value in truncated_results.items():
                print(f"{key}: {value}")
            
            # Export key variables to file
            export_dir = "/home/luisvinatea/Dev/Repos/Aquaculture/reports/experiments"
            os.makedirs(export_dir, exist_ok=True)  # Create directory if it doesn't exist
            filename = os.path.join(export_dir, 
                                  f"results_{model_type.value.replace(' ', '_')}_{temperature.value}_{salinity.value}.txt")
            with open(filename, 'w') as f:
                f.write(f"Model: {model_type.value}\n")
                f.write(f"Temperature: {temperature.value} °C\n")
                f.write(f"Salinity: {salinity.value} ‰\n")
                f.write(f"Horse Power: {horsepower.value} HP\n")
                f.write(f"t₁₀: {t10_min.value} min {t10_sec.value} sec ({truncated_t10} minutes)\n")
                f.write(f"t₇₀: {t70_min.value} min {t70_sec.value} sec ({truncated_t70} minutes)\n")
                f.write(f"kWh Price: ${truncated_kwh_price}\n")
                f.write("\nKey Exported Metrics:\n")
                f.write(f"SOTR (kg O₂/h): {truncated_results['SOTR (kg O₂/h)']}\n")
                f.write(f"SAE (kg O₂/kWh): {truncated_results['SAE (kg O₂/kWh)']}\n")
                f.write(f"US$/kg O₂: {truncated_results['US$/kg O₂']}\n")
            print(f"\nResults saved to {filename}")

    calculate_button = widgets.Button(description="Calculate")
    calculate_button.on_click(on_calculate_clicked)
    
    # Display interface
    display(
        widgets.VBox([
            model_type,
            temperature,
            salinity,
            horsepower,
            widgets.HBox([t10_min, t10_sec]),
            widgets.HBox([t70_min, t70_sec]),
            kwh_price,
            calculate_button,
            output
        ])
    )

if __name__ == "__main__":
    create_interface()