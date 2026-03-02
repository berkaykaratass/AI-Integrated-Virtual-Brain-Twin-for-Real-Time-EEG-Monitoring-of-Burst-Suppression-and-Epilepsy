import numpy as np
import matplotlib.pyplot as plt
from backend.src.model.dynamics import KuramotoNetwork
from backend.src.model.connectivity import generate_brain_network
from backend.src.metrics.synchronization import phase_coherence_magnitude

class AdaptiveKuramotoNetwork(KuramotoNetwork):
    """
    Adaptive Kuramoto Model for Burst-Suppression.
    Includes a 'metabolic resource' variable (E) that modulates coupling.
    
    Dynamics:
    dθ/dt = ω + (K * E / N) * Σ A_ij * sin(θ_j - θ_i)
    dE/dt = (1 - E)/τ_rec - β * R * E
    
    where:
    E: Metabolic resource (0 to 1)
    τ_rec: Recovery time constant
    β: Depletion rate (proportional to synchrony R)
    R: Order parameter (global synchrony)
    """
    def __init__(self, *args, recovery_tau=200.0, depletion_rate=2.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.E = 1.0 # Initial energy resource
        self.tau_rec = recovery_tau
        self.beta = depletion_rate
        
    def step_adaptive(self):
        # 1. Calculate standard Kuramoto dTheta but scale K by E
        # Effective coupling is K_eff = K_nominal * E
        current_K = self.K
        self.K = current_K * self.E # Temporarily adjust K for the step
        
        # Calculate R for depletion
        # We need the current phases to calc R before stepping? 
        # Or we can use the previous R. Let's use current phases.
        r = phase_coherence_magnitude(self.phases)
        
        # 2. Update Phases (Standard Step)
        self.step()
        
        # Restore nominal K
        self.K = current_K
        
        # 3. Update Resource E (Euler integration for simplicity)
        # dE/dt = (1 - E)/τ - β * R * E
        dE = (1.0 - self.E) / self.tau_rec - (self.beta * r * self.E)
        self.E += dE * self.dt
        
        # Clip E to be safe
        self.E = np.clip(self.E, 0, 1)
        
        return self.phases, self.E, r

def run_burst_suppression_simulation():
    # Parameters
    N = 100
    T_steps = 2000
    dt = 0.05
    
    # High nominal K to allow bursting when E is high
    K_nominal = 12.0 
    
    # Connectivity
    adj = generate_brain_network(N, method='small_world')
    freqs = np.random.normal(10.0, 2.0, N)
    
    model = AdaptiveKuramotoNetwork(
        N, freqs, adj, 
        coupling_strength=K_nominal, 
        noise_std=1.0, 
        dt=dt,
        recovery_tau=100.0, # Slow recovery
        depletion_rate=0.8  # Fast depletion when synchronized
    )
    
    history_r = []
    history_e = []
    
    print("Starting Burst-Suppression Simulation...")
    for t in range(T_steps):
        _, e, r = model.step_adaptive()
        history_r.append(r)
        history_e.append(e)
        
    # Visualization
    time = np.arange(T_steps) * dt
    
    plt.figure(figsize=(12, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(time, history_r, color='black', lw=1)
    plt.title('Burst-Suppression: Synchronization (R)')
    plt.ylabel('Order (R)')
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    
    plt.subplot(2, 1, 2)
    plt.plot(time, history_e, color='green', lw=2)
    plt.title('Metabolic Resource (E)')
    plt.ylabel('Energy Level')
    plt.xlabel('Time (s)')
    
    plt.tight_layout()
    plt.savefig('burst_suppression_results.png')
    print("Saved burst_suppression_results.png")

if __name__ == "__main__":
    run_burst_suppression_simulation()
