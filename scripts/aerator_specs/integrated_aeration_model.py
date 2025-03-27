import numpy as np
from scipy.optimize import linprog
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.pyplot as plt
import os
from datetime import datetime
from sae_sotr_calculator import ShrimpPondCalculator

# Classes from aerator_depreciation_calculator.py
class Aerator:
    """Class representing an aeration device with cost and performance attributes."""
    def __init__(self, name, hp, capital_cost, useful_life, repair_cost, operating_cost_per_hour, do_rate):
        self.name = name
        self.hp = hp
        self.capital_cost = capital_cost
        self.useful_life = useful_life
        self.repair_cost = repair_cost
        self.operating_cost_per_hour = operating_cost_per_hour
        self.do_rate = do_rate  # kg of DO per hour
        self.depreciation_cost = self.calculate_depreciation()

    def calculate_depreciation(self):
        """Calculate annual depreciation cost using straight-line method."""
        return self.capital_cost / self.useful_life

    def total_cost(self, hours):
        """Calculate total annual cost for given hours of operation."""
        return self.depreciation_cost + (self.operating_cost_per_hour * hours) + self.repair_cost

    def do_output(self, hours):
        """Calculate total DO output for given hours."""
        return self.do_rate * hours

class AerationOptimizer:
    """Class to optimize aeration device selection using linear programming."""
    def __init__(self, aerators, min_do_required, hours):
        self.aerators = aerators
        self.min_do_required = min_do_required
        self.hours = hours

    def setup_optimization(self):
        """Set up the linear programming problem."""
        c = [aerator.total_cost(self.hours) for aerator in self.aerators]
        A = [-aerator.do_output(self.hours) for aerator in self.aerators]  # Negative for >= constraint
        b = [-self.min_do_required]
        bounds = [(0, None) for _ in self.aerators]
        return c, [A], b, bounds

    def optimize(self):
        """Run optimization to minimize total cost."""
        c, A_ub, b_ub, bounds = self.setup_optimization()
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if result.success:
            return {
                "optimal_cost": result.fun,
                "aerator_usage": {self.aerators[i].name: result.x[i] for i in range(len(self.aerators))},
                "depreciation_cost": sum(self.aerators[i].depreciation_cost * result.x[i] for i in range(len(self.aerators)))
            }
        else:
            return {"status": "Optimization failed", "message": result.message}

# Initial aerator data (now focusing on paddlewheels with placeholder values)
initial_aerators = [
    {"brand": "AquaPaddle", "model": "Standard", "version": "V1", "hp": 3, "capital_cost": 2558, "useful_life": 4, "repair_cost": 363, "operating_cost_per_hour": 0.45, "t10": 1, "t70": 8},
    {"brand": "PaddlePro", "model": "Eco", "version": "V2", "hp": 3, "capital_cost": 2600, "useful_life": 5, "repair_cost": 350, "operating_cost_per_hour": 0.50, "t10": 1, "t70": 8},
    {"brand": "HydroWheel", "model": "MaxFlow", "version": "V1", "hp": 3, "capital_cost": 2500, "useful_life": 4, "repair_cost": 370, "operating_cost_per_hour": 0.48, "t10": 1, "t70": 8}
]

# Helper function from offset_model_torque_hp.py
def truncate_to_2_decimals(value):
    """Truncate float to 2 decimal places without rounding"""
    return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

# Integrated financial model
def create_integrated_interface():
    calculator = ShrimpPondCalculator(
        "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
    )
    
    # Global widgets
    temperature_widget = widgets.FloatSlider(value=28, min=20, max=35, step=0.1, description="Temperature (°C):", style={'description_width': 'initial'})
    salinity_widget = widgets.FloatSlider(value=30, min=0, max=40, step=1, description="Salinity (‰):", style={'description_width': 'initial'})
    kwh_price_widget = widgets.FloatSlider(value=0.05, min=0.01, max=0.20, step=0.01, description="kWh Price ($):", style={'description_width': 'initial'})
    aerator_tier = widgets.Text(value='Medium', description='Aerator Tier:', layout={'width': '400px'})
    pond_volume = widgets.IntSlider(value=70, min=10, max=500, step=10, description='Pond Volume (m³):')
    daily_hours = widgets.IntSlider(value=8, min=1, max=24, step=1, description='Daily Hours:', style={'description_width': 'initial'})
    run_button = widgets.Button(description="Run Analysis", button_style='success', tooltip='Click to run the analysis')
    output = widgets.Output()
    
    # Create aerator widgets with brand, model, version, and other parameters
    def create_aerator_widgets(aerator_data):
        widgets_dict = {}
        for aerator in aerator_data:
            # Create a unique identifier for the aerator
            aerator_id = f"{aerator['brand']} {aerator['model']} {aerator['version']}"
            widgets_dict[aerator_id] = {
                "brand": widgets.Text(
                    value=aerator["brand"],
                    description="Brand:",
                    style={'description_width': 'initial'}
                ),
                "model": widgets.Text(
                    value=aerator["model"],
                    description="Model:",
                    style={'description_width': 'initial'}
                ),
                "version": widgets.Text(
                    value=aerator["version"],
                    description="Version:",
                    style={'description_width': 'initial'}
                ),
                "horsepower": widgets.FloatSlider(
                    value=aerator["hp"] if aerator["hp"] is not None else 3,
                    min=0.5, max=20, step=0.5,
                    description="Horse Power:",
                    style={'description_width': 'initial'}
                ),
                "t10": widgets.FloatSlider(
                    value=aerator["t10"],
                    min=0.1, max=5, step=0.1,
                    description="t₁₀ (min):",
                    style={'description_width': 'initial'}
                ),
                "t70": widgets.FloatSlider(
                    value=aerator["t70"],
                    min=1, max=20, step=0.1,
                    description="t₇₀ (min):",
                    style={'description_width': 'initial'}
                ),
                "capital_cost": widgets.FloatSlider(
                    value=aerator["capital_cost"],
                    min=100, max=5000, step=10,
                    description="Capital Cost ($):",
                    style={'description_width': 'initial'}
                ),
                "useful_life": widgets.FloatSlider(
                    value=aerator["useful_life"],
                    min=1, max=15, step=1,
                    description="Useful Life (yr):",
                    style={'description_width': 'initial'}
                ),
                "repair_cost": widgets.FloatSlider(
                    value=aerator["repair_cost"],
                    min=0, max=500, step=5,
                    description="Repair Cost ($):",
                    style={'description_width': 'initial'}
                ),
                "operating_cost": widgets.FloatSlider(
                    value=aerator["operating_cost_per_hour"],
                    min=0, max=15, step=0.01,
                    description="Operating Cost ($/h):",
                    style={'description_width': 'initial'}
                ),
                "do_deficit_factor": widgets.FloatSlider(
                    value=1.0,
                    min=0.5, max=1.5, step=0.05,
                    description="DO Deficit Factor:",
                    style={'description_width': 'initial'}
                ),
                "water_depth_factor": widgets.FloatSlider(
                    value=1.0,
                    min=0.5, max=1.5, step=0.05,
                    description="Water Depth Factor:",
                    style={'description_width': 'initial'}
                ),
                "placement_factor": widgets.FloatSlider(
                    value=1.0,
                    min=0.5, max=1.5, step=0.05,
                    description="Placement Factor:",
                    style={'description_width': 'initial'}
                )
            }
        return widgets_dict

    aerator_widgets = create_aerator_widgets(initial_aerators)
    
    # Save path
    SAVE_PATH = "/home/luisvinatea/Dev/Repos/Aquaculture/reports/experiments"
    os.makedirs(SAVE_PATH, exist_ok=True)

    def plot_cost_comparison(calculated_cost, ideal_cost, subpowered_costs, overpowered_costs, aerator_ids):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Plot 1: Selected vs Ideal HP
        categories = ['Selected HP', 'Ideal HP']
        costs = [calculated_cost, ideal_cost]
        ax1.bar(categories, costs, color=['#FF9999', '#66B2FF'])
        ax1.set_ylabel('US$/kg O₂')
        ax1.set_title('Cost per kg of Transferred Oxygen (Selected vs Ideal)')
        for i, v in enumerate(costs):
            ax1.text(i, v + 0.01, f"{v:.2f}", ha='center')
        
        # Plot 2: Breakeven Analysis for Each Aerator
        x = np.arange(len(aerator_ids))
        width = 0.35
        ax2.bar(x - width/2, subpowered_costs, width, label='Subpowered', color='#FF6666')
        ax2.bar(x + width/2, overpowered_costs, width, label='Overpowered', color='#66CC66')
        ax2.set_ylabel('Total Annual Cost ($)')
        ax2.set_title('Breakeven Analysis: Subpowered vs Overpowered')
        ax2.set_xticks(x)
        ax2.set_xticklabels(aerator_ids, rotation=45, ha='right')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()

    def run_analysis(button):
        with output:
            clear_output(wait=True)
            
            # Get global parameters from widgets
            TEMPERATURE = temperature_widget.value
            SALINITY = salinity_widget.value
            KWH_PRICE = kwh_price_widget.value
            
            # Calculate yearly hours
            yearly_hours = daily_hours.value * 365
            
            # Calculate average horsepower
            global_hp = sum(widget["horsepower"].value for widget in aerator_widgets.values()) / len(aerator_widgets)
            
            # Use the first aerator's parameters for initial SOTR calculation (placeholder)
            first_aerator_id = list(aerator_widgets.keys())[0]
            initial_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, global_hp, pond_volume.value, 
                aerator_widgets[first_aerator_id]["t10"].value, 
                aerator_widgets[first_aerator_id]["t70"].value, 
                KWH_PRICE, first_aerator_id,
                aerator_widgets[first_aerator_id]["do_deficit_factor"].value,
                aerator_widgets[first_aerator_id]["water_depth_factor"].value,
                aerator_widgets[first_aerator_id]["placement_factor"].value
            )
            initial_sotr = initial_metrics["SOTR (kg O₂/h)"]
            initial_total_o2_demand = initial_sotr * yearly_hours  # Placeholder demand
            
            # Calculate ideal HP metrics
            ideal_hp = calculator.get_ideal_hp(pond_volume.value)
            ideal_metrics = calculator.calculate_metrics(
                TEMPERATURE, SALINITY, ideal_hp, pond_volume.value, 
                aerator_widgets[first_aerator_id]["t10"].value, 
                aerator_widgets[first_aerator_id]["t70"].value, 
                KWH_PRICE, first_aerator_id,
                aerator_widgets[first_aerator_id]["do_deficit_factor"].value,
                aerator_widgets[first_aerator_id]["water_depth_factor"].value,
                aerator_widgets[first_aerator_id]["placement_factor"].value
            )
            ideal_volume = calculator.get_ideal_volume(global_hp)
            
            initial_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                              for k, v in initial_metrics.items()}
            ideal_metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                           for k, v in ideal_metrics.items()}
            
            # Update aerators with widget values and dynamically calculated DO rates
            updated_aerators = []
            aerator_metrics = {}  # Store metrics for each aerator for output
            aerator_id_mapping = {}  # Map original aerator_id to updated aerator_id
            for original_aerator_id, widgets in aerator_widgets.items():
                # Update aerator_id based on widget inputs
                updated_aerator_id = f"{widgets['brand'].value} {widgets['model'].value} {widgets['version'].value}"
                aerator_id_mapping[updated_aerator_id] = original_aerator_id  # Map updated to original
                hp = widgets["horsepower"].value
                t10 = widgets["t10"].value
                t70 = widgets["t70"].value
                do_deficit_factor = widgets["do_deficit_factor"].value
                water_depth_factor = widgets["water_depth_factor"].value
                placement_factor = widgets["placement_factor"].value
                
                # Calculate DO rate dynamically using ShrimpPondCalculator
                metrics = calculator.calculate_metrics(
                    TEMPERATURE, SALINITY, hp, pond_volume.value, t10, t70, KWH_PRICE, updated_aerator_id,
                    do_deficit_factor, water_depth_factor, placement_factor
                )
                metrics = {k: truncate_to_2_decimals(v) if isinstance(v, float) else v 
                          for k, v in metrics.items()}
                do_rate = metrics["SOTR (kg O₂/h)"]
                aerator_metrics[updated_aerator_id] = metrics  # Store metrics for output
                
                updated_aerators.append(Aerator(
                    name=updated_aerator_id,
                    hp=hp,
                    capital_cost=widgets["capital_cost"].value,
                    useful_life=widgets["useful_life"].value,
                    repair_cost=widgets["repair_cost"].value,
                    operating_cost_per_hour=widgets["operating_cost"].value,
                    do_rate=do_rate
                ))
            
            # Run optimization to meet initial oxygen demand
            optimizer = AerationOptimizer(updated_aerators, initial_total_o2_demand, yearly_hours)
            result = optimizer.optimize()
            
            # Recalculate total oxygen demand based on selected aerator(s)
            total_o2_demand = 0
            if "aerator_usage" in result:
                for aerator, usage in zip(updated_aerators, result["aerator_usage"].values()):
                    if usage > 0:
                        total_o2_demand += aerator.do_rate * yearly_hours * usage
            else:
                total_o2_demand = initial_total_o2_demand  # Fallback if optimization fails
            
            # Breakeven analysis: Subpowered vs Overpowered for each aerator
            subpowered_costs = []
            overpowered_costs = []
            aerator_ids = [aerator.name for aerator in updated_aerators]
            
            for aerator in updated_aerators:
                updated_aerator_id = aerator.name
                # Use the mapping to get the original aerator_id
                original_aerator_id = aerator_id_mapping[updated_aerator_id]
                widgets = aerator_widgets[original_aerator_id]
                # Subpowered: Use half the aerator's HP (or minimum HP)
                subpowered_hp = max(0.5, aerator.hp / 2)
                subpowered_metrics = calculator.calculate_metrics(
                    TEMPERATURE, SALINITY, subpowered_hp, pond_volume.value,
                    widgets["t10"].value,
                    widgets["t70"].value,
                    KWH_PRICE, updated_aerator_id,
                    widgets["do_deficit_factor"].value,
                    widgets["water_depth_factor"].value,
                    widgets["placement_factor"].value
                )
                subpowered_o2_per_hour = subpowered_metrics["SOTR (kg O₂/h)"]
                subpowered_o2_demand = subpowered_o2_per_hour * yearly_hours
                sub_optimizer = AerationOptimizer([aerator], subpowered_o2_demand, yearly_hours)
                sub_result = sub_optimizer.optimize()
                subpowered_costs.append(sub_result['optimal_cost'] if 'optimal_cost' in sub_result else float('inf'))
                
                # Overpowered: Use double the aerator's HP (or max HP)
                overpowered_hp = min(20, aerator.hp * 2)
                overpowered_metrics = calculator.calculate_metrics(
                    TEMPERATURE, SALINITY, overpowered_hp, pond_volume.value,
                    widgets["t10"].value,
                    widgets["t70"].value,
                    KWH_PRICE, updated_aerator_id,
                    widgets["do_deficit_factor"].value,
                    widgets["water_depth_factor"].value,
                    widgets["placement_factor"].value
                )
                overpowered_o2_per_hour = overpowered_metrics["SOTR (kg O₂/h)"]
                overpowered_o2_demand = overpowered_o2_per_hour * yearly_hours
                over_optimizer = AerationOptimizer([aerator], overpowered_o2_demand, yearly_hours)
                over_result = over_optimizer.optimize()
                overpowered_costs.append(over_result['optimal_cost'] if 'optimal_cost' in over_result else float('inf'))
            
            # Generate filename with specs
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integrated_do_{int(total_o2_demand)}_hours_{yearly_hours}_{timestamp}.txt"
            filepath = os.path.join(SAVE_PATH, filename)
            
            # Prepare output string
            output_str = f"Integrated Analysis\n\n"
            output_str += f"Aerator Tier: {aerator_tier.value}\n"
            output_str += f"Temperature: {TEMPERATURE} °C\n"
            output_str += f"Salinity: {SALINITY} ‰\n"
            output_str += f"Average Horse Power: {global_hp:.2f} HP\n"
            output_str += f"Ideal Horse Power for {pond_volume.value} m³: {ideal_hp} HP\n"
            output_str += f"Selected Pond Volume: {pond_volume.value} m³\n"
            output_str += f"Ideal Pond Volume for {global_hp:.2f} HP: {ideal_volume} m³\n"
            output_str += f"Daily Hours: {daily_hours.value}\n"
            output_str += f"Yearly Hours: {yearly_hours}\n"
            output_str += f"Total Oxygen Demand: {total_o2_demand:.2f} kg O₂/year\n"
            output_str += f"kWh Price: ${KWH_PRICE}\n\n"
            
            output_str += "Aerator-Specific Parameters:\n"
            for aerator in updated_aerators:
                updated_aerator_id = aerator.name
                original_aerator_id = aerator_id_mapping[updated_aerator_id]
                widgets = aerator_widgets[original_aerator_id]
                metrics = aerator_metrics[updated_aerator_id]
                output_str += f"{updated_aerator_id}:\n"
                output_str += f"  Horse Power: {aerator.hp:.2f} HP\n"
                output_str += f"  t₁₀: {widgets['t10'].value} min\n"
                output_str += f"  t₇₀: {widgets['t70'].value} min\n"
                output_str += f"  DO Deficit Factor: {widgets['do_deficit_factor'].value:.2f}\n"
                output_str += f"  Water Depth Factor: {widgets['water_depth_factor'].value:.2f}\n"
                output_str += f"  Placement Factor: {widgets['placement_factor'].value:.2f}\n"
                output_str += f"  Calculated DO Rate: {aerator.do_rate:.2f} kg O₂/h\n"
                output_str += f"  SAE: {metrics['SAE (kg O₂/kWh)']:.2f} kg O₂/kWh\n"
                output_str += f"  KlaT: {metrics['KlaT (h⁻¹)']:.2f} h⁻¹\n"
                output_str += f"  Power: {metrics['Power (kW)']:.2f} kW\n\n"
            
            output_str += "Metrics Comparison (Average HP vs Ideal HP):\n"
            for key in initial_metrics:
                log_var = np.log10(abs(initial_metrics[key] - ideal_metrics[key]) + 1) * (1 if (initial_metrics[key] - ideal_metrics[key]) >= 0 else -1)
                log_var = truncate_to_2_decimals(log_var) if isinstance(initial_metrics[key], float) else 'N/A'
                output_str += f"{key}: {initial_metrics[key]} vs {ideal_metrics[key]} (Log % Variation: {log_var})\n"
            
            output_str += "\nOptimization Results:\n"
            if "optimal_cost" in result:
                output_str += f"Optimal Total Cost: ${result['optimal_cost']:.2f}\n"
                output_str += f"Depreciation Cost: ${result['depreciation_cost']:.2f}\n"
                output_str += "Aerator Usage:\n"
                for name, usage in result["aerator_usage"].items():
                    if usage > 0:
                        output_str += f"  {name}: {usage:.2f} units\n"
            else:
                output_str += f"Status: {result['status']}\n"
                output_str += f"Message: {result['message']}\n"
            
            output_str += "\nBreakeven Analysis (Subpowered vs Overpowered):\n"
            for i, aerator_id in enumerate(aerator_ids):
                output_str += f"{aerator_id}:\n"
                output_str += f"  Subpowered Cost (HP={max(0.5, updated_aerators[i].hp / 2):.2f}): ${subpowered_costs[i]:.2f}\n"
                output_str += f"  Overpowered Cost (HP={min(20, updated_aerators[i].hp * 2):.2f}): ${overpowered_costs[i]:.2f}\n"
            
            # Save to file
            with open(filepath, 'w') as f:
                f.write(output_str)
            
            # Print to output
            print(output_str)
            print(f"Results saved to: {filepath}")
            
            # Plot comparisons
            plot_cost_comparison(initial_metrics['US$/kg O₂'], ideal_metrics['US$/kg O₂'], subpowered_costs, overpowered_costs, aerator_ids)

    # Connect button to function
    run_button.on_click(run_analysis)

    # Layout with Accordion for aerator settings
    global_controls = widgets.VBox(
        [widgets.Label("Global Settings", layout={'font_weight': 'bold'}),
         aerator_tier,
         pond_volume,
         daily_hours,
         temperature_widget,
         salinity_widget,
         kwh_price_widget,
         run_button],
        layout={'padding': '10px'}
    )

    # Create an Accordion for aerator settings
    accordion_items = []
    for aerator_id, widget_group in aerator_widgets.items():
        accordion_items.append(widgets.VBox(
            [widgets.Label(f"{aerator_id} Settings", layout={'font_weight': 'bold'}),
             *widget_group.values()],
            layout={'padding': '5px'}
        ))

    accordion = widgets.Accordion(children=accordion_items, layout={'width': '600px'})
    for i, aerator_id in enumerate(aerator_widgets.keys()):
        accordion.set_title(i, aerator_id)

    # Main layout
    ui = widgets.VBox(
        [widgets.Label("Integrated Aeration Financial Model", layout={'font_weight': 'bold', 'font_size': '16px', 'padding': '0px'}),
         widgets.HBox([global_controls, accordion], layout={'padding': '10px'})],
        layout={'border': '1px solid gray', 'padding': '10px'}
    )

    # Display interface
    display(ui, output)

if __name__ == "__main__":
    create_integrated_interface()