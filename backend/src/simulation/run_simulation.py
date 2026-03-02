import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from backend.src.model.dynamics import KuramotoNetwork
from backend.src.model.connectivity import generate_brain_network
from backend.src.metrics.synchronization import phase_coherence_magnitude, synchronization_entropy

def run_seizure_simulation():
    # Simulation Parameters
    N = 100               # Number of nodes
    T = 1000              # Number of time steps
    dt = 0.05             # Time step size
    noise_std = 0.5       # Noise level to keep it realistic
    
    # 1. Generate Brain Network (Small-World)
    print("Generating Brain Network (Small-World)...")
    adj_matrix = generate_brain_network(N, method='small_world', k=6, p=0.1)
    
    # 2. Initialize Natural Frequencies (Gamma Band: 30-80 Hz, usually simplified model uses arb units)
    # Here we use a normal distribution centered around a mean frequency
    mean_freq = 10.0 # rad/s (approx 1.6 Hz base, just for model scale)
    std_freq = 2.0
    natural_freqs = np.random.normal(mean_freq, std_freq, N)
    
    # 3. Setup Simulation Loop
    # We will dynamically change Coupling Strength (K) to simulate Seizure Onset
    # t=0-300: Normal (K low)
    # t=300-700: Seizure Onset (K high) -> Hypersynchrony
    # t=700-1000: Post-ictal / Recovery (K drops)
    
    K_baseline = 0.5
    K_seizure = 8.0
    
    # History arrays
    order_params = []
    entropies = []
    time_points = []
    
    # Initialize Model
    model = KuramotoNetwork(N, natural_freqs, adj_matrix, coupling_strength=K_baseline, noise_std=noise_std, dt=dt)
    
    print("Starting Simulation...")
    for t in range(T):
        # Dynamic Coupling Control
        if 300 <= t < 700:
            # Ramping up to seizure
            model.K = K_seizure
        else:
            model.K = K_baseline
            
        # Step
        phases = model.step()
        
        # Calculate Metrics
        r = phase_coherence_magnitude(phases)
        s = synchronization_entropy(phases)
        
        order_params.append(r)
        entropies.append(s)
        time_points.append(t * dt)
        
    print("Simulation Complete.")
    
    # 4. Visualization
    plt.figure(figsize=(12, 8))
    
    # Plot 1: Order Parameter (Synchronization)
    plt.subplot(2, 1, 1)
    plt.plot(time_points, order_params, label='Order Parameter (R)', color='blue', linewidth=2)
    plt.axvspan(300*dt, 700*dt, color='red', alpha=0.1, label='Seizure Zone (High K)')
    plt.title('Network Synchronization over Time')
    plt.ylabel('Order Parameter R')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Plot 2: Entropy
    plt.subplot(2, 1, 2)
    plt.plot(time_points, entropies, label='Phase Entropy', color='orange', linewidth=2)
    plt.axvspan(300*dt, 700*dt, color='red', alpha=0.1)
    plt.title('Network Signal Entropy')
    plt.xlabel('Time (s)')
    plt.ylabel('Entropy')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('seizure_simulation_results.png')
    print("Results saved to seizure_simulation_results.png")

if __name__ == "__main__":
    run_seizure_simulation()
