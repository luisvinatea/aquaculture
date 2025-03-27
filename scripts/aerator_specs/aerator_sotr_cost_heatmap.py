import numpy as np
import matplotlib.pyplot as plt
from sae_sotr_calculator import ShrimpPondCalculator

# Fixed parameters
TEMPERATURE = 28
SALINITY = 30
T10 = 1
T70 = 8
KWH_PRICE = 0.05
TARGET_RPM = 125
HP = 3  # Default to 3 HP
VOLUME = 70  # Default to 70 m³ (ideal for 3 HP)

# Initialize calculator
calculator = ShrimpPondCalculator(
    "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
)

def truncate_to_2_decimals(value):
    """Truncate float to 2 decimal places without rounding"""
    return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

def calculate_cost(temp, sal):
    """Calculate US$/kg O₂ for given temperature and salinity"""
    metrics = calculator.calculate_metrics(temp, sal, HP, VOLUME, T10, T70, KWH_PRICE)
    return truncate_to_2_decimals(metrics["US$/kg O₂"])

def plot_4_quadrant_heatmap():
    # Temperature and salinity ranges from metadata
    temp_range = np.arange(0, 41, 1)  # 0 to 40°C, step 1
    sal_range = np.arange(0, 41, 5)   # 0 to 40‰, step 5
    
    # Create a 2D array for costs
    costs = np.zeros((len(temp_range), len(sal_range)))
    for i, temp in enumerate(temp_range):
        for j, sal in enumerate(sal_range):
            costs[i, j] = calculate_cost(temp, sal)
    
    # Define quadrant boundaries (median values)
    temp_mid = 20  # Midpoint of 0–40°C
    sal_mid = 20   # Midpoint of 0–40‰
    
    # Split data into 4 quadrants
    temp_idx_mid = len(temp_range) // 2  # Index for 20°C
    sal_idx_mid = len(sal_range) // 2    # Index for 20‰
    
    # Create a 2x2 subplot grid with constrained_layout
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharex="col", sharey="row", constrained_layout=True)
    
    # Define quadrant data
    quadrants = [
        (costs[:temp_idx_mid, :sal_idx_mid], "Low Temp, Low Sal", axes[0, 0], temp_range[:temp_idx_mid], sal_range[:sal_idx_mid]),
        (costs[:temp_idx_mid, sal_idx_mid:], "Low Temp, High Sal", axes[0, 1], temp_range[:temp_idx_mid], sal_range[sal_idx_mid:]),
        (costs[temp_idx_mid:, :sal_idx_mid], "High Temp, Low Sal", axes[1, 0], temp_range[temp_idx_mid:], sal_range[:sal_idx_mid]),
        (costs[temp_idx_mid:, sal_idx_mid:], "High Temp, High Sal", axes[1, 1], temp_range[temp_idx_mid:], sal_range[sal_idx_mid:])
    ]
    
    # Plot each quadrant
    for cost_data, title, ax, temp_subset, sal_subset in quadrants:
        im = ax.imshow(cost_data, cmap="YlOrRd", aspect="auto", origin="lower")
        ax.set_title(title)
        
        # Set tick labels
        temp_ticks = np.linspace(0, len(temp_subset) - 1, 5, dtype=int)
        sal_ticks = np.linspace(0, len(sal_subset) - 1, 3, dtype=int)
        ax.set_xticks(sal_ticks)
        ax.set_yticks(temp_ticks)
        ax.set_xticklabels([int(sal_subset[i]) for i in sal_ticks])
        ax.set_yticklabels([int(temp_subset[i]) for i in temp_ticks])
        
        # Label axes
        if ax in axes[-1, :]:  # Bottom row
            ax.set_xlabel("Salinity (‰)")
        if ax in axes[:, 0]:   # Left column
            ax.set_ylabel("Temperature (°C)")
    
    # Add a colorbar
    fig.colorbar(im, ax=axes.ravel().tolist(), label="US$/kg O₂", orientation="vertical")
    
    # Overall title
    plt.suptitle("Cost per kg of Transferred Oxygen Across Temperature and Salinity", fontsize=16)
    plt.show()

    # Print summary statistics for each quadrant
    print("\nSummary Statistics for Each Quadrant:")
    for cost_data, title, _, _, _ in quadrants:
        avg_cost = truncate_to_2_decimals(np.mean(cost_data))
        min_cost = truncate_to_2_decimals(np.min(cost_data))
        max_cost = truncate_to_2_decimals(np.max(cost_data))
        print(f"{title}:")
        print(f"  Average Cost: ${avg_cost}/kg O₂")
        print(f"  Min Cost: ${min_cost}/kg O₂")
        print(f"  Max Cost: ${max_cost}/kg O₂")

if __name__ == "__main__":
    print("Plotting 4-Quadrant Cost Heatmap...")
    plot_4_quadrant_heatmap()