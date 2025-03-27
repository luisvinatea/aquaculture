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

calculator = ShrimpPondCalculator(
    "/home/luisvinatea/Dev/Repos/Aquaculture/data/raw/json/o2_temp_sal_100_sat.json"
)

def truncate_to_2_decimals(value):
    """Truncate float to 2 decimal places without rounding"""
    return float(f"{value:.2f}"[:f"{value:.2f}".index('.') + 3])

def calculate_metrics(hp, volume):
    metrics = calculator.calculate_metrics(TEMPERATURE, SALINITY, hp, volume, T10, T70, KWH_PRICE)
    return {k: truncate_to_2_decimals(v) if isinstance(v, float) else v for k, v in metrics.items()}

def torque(hp):
    power_w = hp * 746
    angular_velocity = (TARGET_RPM * 2 * np.pi) / 60
    return power_w / angular_velocity

def plot_efficiency_curve(threshold_volume):
    volumes = np.arange(10, 151, 10)
    sae_2hp = [calculate_metrics(2, vol)["SAE (kg O₂/kWh)"] for vol in volumes]
    sae_3hp = [calculate_metrics(3, vol)["SAE (kg O₂/kWh)"] for vol in volumes]
    
    # Calculate slopes (vector directions) for SAE
    sae_slope_2hp = (sae_2hp[-1] - sae_2hp[0]) / (volumes[-1] - volumes[0])
    sae_slope_3hp = (sae_3hp[-1] - sae_3hp[0]) / (volumes[-1] - volumes[0])
    
    plt.figure(figsize=(10, 6))
    plt.plot(volumes, sae_2hp, label="2 HP", color="blue", marker="o")
    plt.plot(volumes, sae_3hp, label="3 HP", color="red", marker="o")
    plt.axvline(x=40, color="blue", linestyle="--", label="Ideal 2 HP (40 m³)")
    plt.axvline(x=70, color="red", linestyle="--", label="Ideal 3 HP (70 m³)")
    plt.axvline(x=threshold_volume, color="green", linestyle="-.", label=f"2 HP Torque Threshold ({threshold_volume} m³)")
    plt.xlabel("Pond Volume (m³)")
    plt.ylabel("SAE (kg O₂/kWh)")
    plt.title("Aeration Efficiency vs Pond Volume")
    plt.legend()
    plt.grid(True)
    plt.show()

    print(f"\nSAE Vector Directions (Slopes):")
    print(f"2 HP SAE Slope: {truncate_to_2_decimals(sae_slope_2hp)} kg O₂/kWh per m³")
    print(f"3 HP SAE Slope: {truncate_to_2_decimals(sae_slope_3hp)} kg O₂/kWh per m³")

    # Test cases
    test_cases = [
        {"hp": 2, "volume": 70, "label": "2 HP in 70 m³"},
        {"hp": 3, "volume": 40, "label": "3 HP in 40 m³"}
    ]
    
    savings_analysis = []
    for case in test_cases:
        metrics = calculate_metrics(case["hp"], case["volume"])
        ideal_hp = calculator.get_ideal_hp(case["volume"])
        ideal_metrics = calculate_metrics(ideal_hp, case["volume"])
        print(f"\n{case['label']}:")
        print(f"Selected HP: {case['hp']}, Ideal HP: {ideal_hp}")
        print(f"Volume: {case['volume']} m³")
        for key in metrics:
            diff = metrics[key] - ideal_metrics[key]
            log_var = truncate_to_2_decimals(np.log10(abs(diff) + 1) * (1 if diff >= 0 else -1))
            print(f"{key}: {metrics[key]} vs {ideal_metrics[key]} (Log % Variation: {log_var})")
        
        # Savings analysis
        cost_diff = metrics["US$/kg O₂"] - ideal_metrics["US$/kg O₂"]
        savings = -cost_diff  # Negative cost difference = savings
        feasible = case["volume"] <= threshold_volume if case["hp"] == 2 else True
        savings_analysis.append({
            "label": case["label"],
            "savings": truncate_to_2_decimals(savings),
            "feasible": feasible
        })
    
    print("\nSavings Analysis:")
    for analysis in savings_analysis:
        print(f"{analysis['label']}: Savings = ${analysis['savings']} per kg O₂, Feasible = {analysis['feasible']}")

def find_torque_threshold():
    torque_2hp = torque(2)
    torque_3hp = torque(3)
    volumes = np.arange(10, 151, 10)
    sotr_2hp = [calculate_metrics(2, vol)["SOTR (kg O₂/h)"] for vol in volumes]
    
    ideal_sotr_3hp = calculate_metrics(3, 70)["SOTR (kg O₂/h)"]
    k = torque_3hp / ideal_sotr_3hp
    torque_demands = [k * sotr for sotr in sotr_2hp]
    
    threshold_volume = None
    for vol, demand in zip(volumes, torque_demands):
        if demand > torque_2hp:
            threshold_volume = vol
            break
    
    print(f"\nTorque Analysis:")
    print(f"2 HP Torque Capacity: {truncate_to_2_decimals(torque_2hp)} Nm")
    print(f"3 HP Torque Capacity: {truncate_to_2_decimals(torque_3hp)} Nm")
    print(f"Estimated Torque Demand Coefficient: {truncate_to_2_decimals(k)} Nm per kg O₂/h")
    if threshold_volume:
        print(f"Threshold Volume where 2 HP fails: {threshold_volume} m³")
        print(f"Torque Demand at {threshold_volume} m³: {truncate_to_2_decimals(torque_demands[volumes.tolist().index(threshold_volume)])} Nm")
    else:
        print("2 HP can handle all tested volumes up to 150 m³")

    plt.figure(figsize=(10, 6))
    plt.plot(volumes, torque_demands, label="Torque Demand", color="green", marker="o")
    plt.axhline(y=torque_2hp, color="blue", linestyle="--", label="2 HP Capacity")
    plt.axhline(y=torque_3hp, color="red", linestyle="--", label="3 HP Capacity")
    plt.xlabel("Pond Volume (m³)")
    plt.ylabel("Torque (Nm)")
    plt.title("Torque Demand vs Capacity")
    plt.legend()
    plt.grid(True)
    plt.show()

    return threshold_volume

if __name__ == "__main__":
    print("Calculating Torque Threshold...")
    threshold_volume = find_torque_threshold()
    print("\nPlotting Efficiency Curve with Threshold...")
    plot_efficiency_curve(threshold_volume)