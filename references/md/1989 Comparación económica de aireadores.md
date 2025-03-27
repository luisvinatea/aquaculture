# An Economic Comparison of Aeration Devices for Aquaculture Ponds

**Author:** Carole R. Engle
**Published:** Aquacultural Engineering 8 (1989) 193-207
**Affiliation:** Department of Agriculture, University of Arkansas at Pine Bluff, Pine Bluff, Arkansas 71601, USA
**Received:** 1 December 1988
**Accepted:** 10 March 1989

## Abstract

This study uses an economic engineering approach to estimate total aeration costs and generate average cost curves for 23 electric and tractor-powered aeration devices in catfish ponds. Fixed and variable costs were calculated, and least-cost devices were identified for varying pond sizes and aeration durations. Tractor-powered devices were more economical below 250 hours of aeration per season, while electric aerators were more efficient above 250 hours. For ponds under 2 ha, propeller-aspirator-pumps (1-3 hp) were the least-cost option, while electric floating paddlewheels were most efficient for ponds over 0.4 ha.

---

## Notation

- **A**: $m \times n$ matrix of technical coefficients
- **AC/kg DO**: Average Total Cost per kilogram of dissolved oxygen transferred
- **ATC**: Average Total Cost $TC/Q$
- **B**: $m \times 1$ vector of constraints
- **C**: Objective function of the linear programming model
- **E**: $1 \times m$ vector of coefficients associated with each activity
- **Q**: Quantity of output
- **TC**: Total Cost $TFC + TVC$
- **TFC**: Total Fixed Cost
- **TVC**: Total Variable Cost
- **X**: $1 \times n$ vector of activities

---

## Introduction

Catfish farmers increasingly rely on aeration devices to maintain dissolved oxygen (DO) levels in ponds, as low DO reduces weight gain, feed conversion, and increases disease susceptibility. This study estimates total costs and generates average cost curves for aeration devices tested at Auburn University (Boyd & Ahmad, 1987). It compares tractor-powered (e.g., pump sprayers, paddlewheels) and electric-powered (e.g., paddlewheels, vertical pumps, propeller-aspirator-pumps, diffusers) systems, focusing on economic efficiency rather than a comprehensive equipment review.

---

## Theoretical Considerations

Aeration is an input to fish production, akin to fertilizer, involving fixed costs (e.g., depreciation) and variable costs (e.g., operating expenses). Total Cost (TC) is calculated as:

$TFC + TVC = TC$

Average Total Cost (ATC) measures efficiency:

$ATC = \frac{TC}{Q}$

Where:

- $TFC$: Total Fixed Cost
- $TVC$: Total Variable Cost
- $TC$: Total Cost
- $Q$: Quantity of Output (kg of DO)
- $ATC$: Average Total Cost

The study uses kg of DO as the output metric and employs an economic engineering approach to analyze costs.

---

## Materials and Methods

Data were collected via telephone interviews with 17 aerator manufacturers for capital costs and with motor/gearbox manufacturers for repair costs. Depreciation was calculated using the straight-line method, with useful life estimated from construction materials. Operating costs were based on \$0.075/kWh (Boyd & Ahmad, 1987). Average cost (AC/kg DO) was computed for 50–1850 hours of annual aeration. A linear programming model minimized total annual cost:

$\text{Minimize } C = E \cdot X$  
$\text{Subject to } A \cdot X \geq B$  
$X \geq 0$

---

## Results and Discussion

### Capital Investment and Depreciation

Capital costs ranged from \$450 to \$3500, with annual depreciation from \$183 to \$1426 (Table 1). Electric paddlewheels had the highest mean capital cost, while propeller-aspirator-pumps were the lowest.

**Table 1: Capital Investment and Depreciation Costs**

| Aerator Type             | hp Range  | Capital Investment ($) | Useful Life (years) | Annual Depreciation ($) |
|--------------------------|-----------|------------------------|---------------------|-------------------------|
| Floating Paddlewheels    | 2–10      | 1045–3000              | 2–6                 | 261–1325                |
| Floating Vertical Pump   | 0.33–10   | 450–2852               | 1–3                 | 225–1426                |
| Floating Pump Sprayer    | 10–20     | 2450–2625              | 3–5                 | 490–833                 |
| Diffuser                 | 0.75–1.7  | 925–3500               | 3–5                 | 411–412                 |
| Propeller-Aspirator-Pump | 0.5–3.0   | 550–750                | 3–3                 | 183–250                 |
| Tractor Paddlewheel      | na        | 2650                   | 10                  | 265                     |
| Tractor Pump Sprayer     | na        | 2350–3000              | 10                  | 235–300                 |

### Repair and Maintenance Costs

Repair costs ranged from $44 to $450 annually (Table 2), with pump sprayers highest due to larger motors and paddlewheels higher due to gear complexity.

**Table 2: Repair and Maintenance Costs**

| Aerator Type             | Electric Motor Cost ($) | Gear Cost ($) | Total Repair Cost ($) | Cost/hp ($) |
|--------------------------|-------------------------|---------------|-----------------------|-------------|
| Floating Paddlewheels    | 55–120                  | 104–300       | 159–420               | 38–80       |
| Floating Vertical Pump   | 44–120                  | na            | 44–120                | 11–133      |
| Floating Pump Sprayer    | 108–450                 | na            | 108–450               | 11–22       |
| Diffuser                 | 48–110                  | na            | 48–110                | 64–65       |
| Propeller-Aspirator-Pump | 45–55                   | na            | 45–50                 | 18–90       |

### Operating Costs

Operating costs ranged from $0.025 to $1.42/h for electric aerators and $12/h for tractor-powered units (Table 3). Tractor costs dominated total costs (75–86%), while electric aerator operating costs were 4–49%.

**Table 3: Operating Costs**

| Aerator Type             | Cost/h ($) | Cost/hp-h ($) |
|--------------------------|------------|---------------|
| Floating Paddlewheels    | 0.15–0.75  | ~0.075        |
| Floating Vertical Pump   | 0.025–0.75 | ~0.075        |
| Floating Pump Sprayer    | 0.75–1.42  | ~0.075        |
| Diffuser                 | 0.056–0.13 | ~0.075        |
| Propeller-Aspirator-Pump | 0.038–0.23 | ~0.075        |
| Tractor Paddlewheel      | 12.00      | na            |
| Tractor Pump Sprayer     | 12.00      | na            |

---

## Python Implementation

Below are Python methods to compute the costs and average cost curves described in the study.

```python
import numpy as np
import matplotlib.pyplot as plt

# Constants
ELECTRICITY_COST = 0.075  # $/kWh
TRACTOR_COST = 12.00      # $/h (representative)

# Aerator data: [hp, capital ($), useful life (years), repair ($), operating ($/h), DO rate (kg/h)]
aerators = {
    "Floating Paddlewheels": [6, 2558, 4, 363, 0.45, 1.5],  # Mean values
    "Floating Vertical Pump": [3, 1619, 2, 69, 0.225, 1.0],
    "Floating Pump Sprayer": [17, 2525, 4, 336, 1.085, 2.0],
    "Diffuser": [1, 2212, 4, 79, 0.093, 0.8],
    "Propeller-Aspirator-Pump": [1.5, 650, 3, 50, 0.134, 1.2],
    "Tractor Paddlewheel": [None, 2650, 10, 0, 12.00, 2.5],
    "Tractor Pump Sprayer": [None, 2683, 10, 0, 12.00, 2.0]
}

def calculate_fixed_cost(capital, useful_life):
    """Calculate annual depreciation cost using straight-line method."""
    return capital / useful_life

def calculate_variable_cost(hours, operating_cost, repair_cost):
    """Calculate total variable cost for given hours."""
    return (operating_cost * hours) + repair_cost

def calculate_total_cost(fixed_cost, variable_cost):
    """Calculate total cost."""
    return fixed_cost + variable_cost

def calculate_ac_per_kg_do(total_cost, hours, do_rate):
    """Calculate average cost per kg of dissolved oxygen."""
    total_do = do_rate * hours
    return total_cost / total_do if total_do > 0 else float('inf')

def simulate_aeration_costs(hours_range):
    """Simulate costs for all aerators over a range of hours."""
    results = {}
    for name, (hp, capital, life, repair, op_cost, do_rate) in aerators.items():
        fixed_cost = calculate_fixed_cost(capital, life)
        costs = []
        ac_kg_do = []
        for hours in hours_range:
            var_cost = calculate_variable_cost(hours, op_cost, repair)
            total_cost = calculate_total_cost(fixed_cost, var_cost)
            ac = calculate_ac_per_kg_do(total_cost, hours, do_rate)
            costs.append(total_cost)
            ac_kg_do.append(ac)
        results[name] = {"total_cost": costs, "ac_kg_do": ac_kg_do}
    return results

# Simulate and plot
hours_range = np.arange(50, 1851, 100)
results = simulate_aeration_costs(hours_range)

# Plot Average Cost Curves
plt.figure(figsize=(10, 6))
for name, data in results.items():
    plt.plot(hours_range, data["ac_kg_do"], label=name)
plt.xlabel("Hours of Aeration per Season")
plt.ylabel("Average Cost per kg DO ($/kg)")
plt.title("Average Cost Curves for Aeration Devices")
plt.legend()
plt.grid(True)
plt.show()

# Example: Least-cost analysis for 250 hours
hours = 250
print(f"\nTotal Costs and AC/kg DO at {hours} hours:")
for name, data in results.items():
    total_cost = data["total_cost"][hours_range.tolist().index(hours)]
    ac_kg_do = data["ac_kg_do"][hours_range.tolist().index(hours)]
    print(f"{name}: Total Cost = ${total_cost:.2f}, AC/kg DO = ${ac_kg_do:.2f}")
```

### Explanation of Python Code

1. **Data Structure**: The `aerators` dictionary stores mean values for horsepower, capital cost, useful life, repair cost, operating cost, and DO transfer rate (assumed based on typical performance data).
2. **Cost Functions**:
   - `calculate_fixed_cost`: Computes annual depreciation.
   - `calculate_variable_cost`: Sums operating and repair costs.
   - `calculate_total_cost`: Adds fixed and variable costs.
   - `calculate_ac_per_kg_do`: Computes average cost per kg of DO.
3. **Simulation**: `simulate_aeration_costs` calculates costs across a range of hours (50–1850).
4. **Visualization**: Plots average cost curves to compare efficiency.
5. **Example Output**: Prints costs at 250 hours for comparison.

---

## Conclusion

Tractor-powered aerators are cost-efficient for low aeration durations (<250 h), while electric aerators excel at higher durations. Propeller-aspirator-pumps are optimal for small ponds (<2 ha), and paddlewheels for larger ponds (>0.4 ha). Farmers should weigh construction quality and operating efficiency when selecting devices.

---
