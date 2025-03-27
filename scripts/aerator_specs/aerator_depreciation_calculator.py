import numpy as np
from scipy.optimize import linprog
import ipywidgets as widgets
from IPython.display import display, clear_output
import os
from datetime import datetime

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

# Initial aerator data (mean values from Tables 1-3)
initial_aerators = [
    {"name": "Floating Paddlewheels", "hp": 6, "capital_cost": 2558, "useful_life": 4, "repair_cost": 363, "operating_cost_per_hour": 0.45, "do_rate": 1.5},
    {"name": "Floating Vertical Pump", "hp": 3, "capital_cost": 1619, "useful_life": 2, "repair_cost": 69, "operating_cost_per_hour": 0.225, "do_rate": 1.0},
    {"name": "Floating Pump Sprayer", "hp": 17, "capital_cost": 2525, "useful_life": 4, "repair_cost": 336, "operating_cost_per_hour": 1.085, "do_rate": 2.0},
    {"name": "Diffuser", "hp": 1, "capital_cost": 2212, "useful_life": 4, "repair_cost": 79, "operating_cost_per_hour": 0.093, "do_rate": 0.8},
    {"name": "Propeller-Aspirator-Pump", "hp": 1.5, "capital_cost": 650, "useful_life": 3, "repair_cost": 50, "operating_cost_per_hour": 0.134, "do_rate": 1.2},
    {"name": "Tractor Paddlewheel", "hp": None, "capital_cost": 2650, "useful_life": 10, "repair_cost": 0, "operating_cost_per_hour": 12.00, "do_rate": 2.5},
    {"name": "Tractor Pump Sprayer", "hp": None, "capital_cost": 2683, "useful_life": 10, "repair_cost": 0, "operating_cost_per_hour": 12.00, "do_rate": 2.0}
]

# Create widget interface
def create_aerator_widgets(aerator_data):
    """Create widgets for each aerator's parameters."""
    widgets_dict = {}
    for aerator in aerator_data:
        name = aerator["name"]
        widgets_dict[name] = {
            "capital_cost": widgets.FloatSlider(value=aerator["capital_cost"], min=100, max=5000, step=10, description="Capital Cost ($):", style={'description_width': 'initial'}),
            "useful_life": widgets.FloatSlider(value=aerator["useful_life"], min=1, max=15, step=1, description="Useful Life (yr):", style={'description_width': 'initial'}),
            "repair_cost": widgets.FloatSlider(value=aerator["repair_cost"], min=0, max=500, step=5, description="Repair Cost ($):", style={'description_width': 'initial'}),
            "operating_cost": widgets.FloatSlider(value=aerator["operating_cost_per_hour"], min=0, max=15, step=0.01, description="Operating Cost ($/h):", style={'description_width': 'initial'}),
            "do_rate": widgets.FloatSlider(value=aerator["do_rate"], min=0.1, max=5, step=0.1, description="DO Rate (kg/h):", style={'description_width': 'initial'})
        }
    return widgets_dict

# Global widgets
min_do_widget = widgets.FloatSlider(value=500, min=100, max=2000, step=10, description="Min DO Required (kg):", style={'description_width': 'initial'})
hours_widget = widgets.IntSlider(value=250, min=50, max=1850, step=10, description="Hours of Aeration:", style={'description_width': 'initial'})
run_button = widgets.Button(description="Run Experiment", button_style='success', tooltip='Click to run the experiment')
aerator_widgets = create_aerator_widgets(initial_aerators)
output = widgets.Output()

# Save path
SAVE_PATH = "/home/luisvinatea/Dev/Repos/Aquaculture/reports/experiments"
os.makedirs(SAVE_PATH, exist_ok=True)

# Optimization and save function
def run_experiment(button):
    """Run optimization and save results when button is clicked."""
    with output:
        clear_output(wait=True)
        
        # Update aerators with widget values
        updated_aerators = []
        for data in initial_aerators:
            name = data["name"]
            updated_aerators.append(Aerator(
                name=name,
                hp=data["hp"],
                capital_cost=aerator_widgets[name]["capital_cost"].value,
                useful_life=aerator_widgets[name]["useful_life"].value,
                repair_cost=aerator_widgets[name]["repair_cost"].value,
                operating_cost_per_hour=aerator_widgets[name]["operating_cost"].value,
                do_rate=aerator_widgets[name]["do_rate"].value
            ))
        
        # Run optimization
        optimizer = AerationOptimizer(updated_aerators, min_do_widget.value, hours_widget.value)
        result = optimizer.optimize()
        
        # Generate filename with specs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"experiment_do_{int(min_do_widget.value)}_hours_{hours_widget.value}_{timestamp}.txt"
        filepath = os.path.join(SAVE_PATH, filename)
        
        # Prepare output string
        output_str = f"Experiment Specs:\nMin DO Required: {min_do_widget.value} kg\nHours: {hours_widget.value}\n\n"
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
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(output_str)
        
        # Print to output
        print(output_str)
        print(f"Results saved to: {filepath}")

# Connect button to function
run_button.on_click(run_experiment)

# Layout with Accordion for aerator settings
global_controls = widgets.VBox(
    [widgets.Label("Global Settings", layout={'font_weight': 'bold'}),
     min_do_widget,
     hours_widget,
     run_button],
    layout={'padding': '10px'}
)

# Create an Accordion for aerator settings
accordion_items = []
for name, widget_group in aerator_widgets.items():
    accordion_items.append(widgets.VBox(
        [widgets.Label(f"{name} Settings", layout={'font_weight': 'bold'}),
         *widget_group.values()],
        layout={'padding': '5px'}
    ))

accordion = widgets.Accordion(children=accordion_items, layout={'width': '600px'})
for i, name in enumerate(aerator_widgets.keys()):
    accordion.set_title(i, name)

# Main layout
ui = widgets.VBox(
    [widgets.Label("Aeration Cost Optimization", layout={'font_weight': 'bold', 'font_size': '16px', 'padding': '10px'}),
     widgets.HBox([global_controls, accordion], layout={'padding': '10px'})],
    layout={'border': '1px solid gray', 'padding': '10px'}
)

# Display interface
display(ui, output)