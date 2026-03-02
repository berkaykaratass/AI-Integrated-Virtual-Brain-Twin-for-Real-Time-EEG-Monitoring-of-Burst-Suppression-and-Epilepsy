import numpy as np

class KuramotoNetwork:
    """
    Kuramoto Model of coupled phase oscillators.
    
    Equation:
    dθ_i/dt = ω_i + (K/N) * Σ_j A_ij * sin(θ_j - θ_i) + noise
    """
    
    def __init__(self, n_oscillators: int, natural_freqs: np.ndarray, 
                 coupling_matrix: np.ndarray, coupling_strength: float = 1.0, 
                 noise_std: float = 0.0, dt: float = 0.01):
        """
        Initialize the Kuramoto Network.
        
        Args:
            n_oscillators (int): Number of nodes.
            natural_freqs (np.ndarray): Intrinsic frequencies (ω) in radians/sec.
            coupling_matrix (np.ndarray): Adjacency matrix (A_ij), typically binary or weighted.
            coupling_strength (float): Global scaling parameter (K).
            noise_std (float): Standard deviation of Gaussian noise.
            dt (float): Time step for integration.
        """
        self.N = n_oscillators
        self.omega = natural_freqs
        self.A = coupling_matrix
        self.K = coupling_strength
        self.noise_std = noise_std
        self.dt = dt
        
        # Initialize phases randomly between 0 and 2π
        self.phases = np.random.uniform(0, 2 * np.pi, self.N)
        
    def derivative(self, phases: np.ndarray) -> np.ndarray:
        """
        Computes dθ/dt for the current phases.
        """
        # Calculate phase differences: sin(θ_j - θ_i)
        # Using broadcasting: diff[i, j] = θ_j - θ_i
        phase_diffs = phases[np.newaxis, :] - phases[:, np.newaxis]
        interaction = np.sum(self.A * np.sin(phase_diffs), axis=1)
        
        dtheta = self.omega + (self.K / self.N) * interaction
        return dtheta

    def step(self):
        """
        Performs one time step of integration using Runge-Kutta 4 (RK4).
        """
        theta = self.phases
        dt = self.dt
        
        k1 = self.derivative(theta)
        k2 = self.derivative(theta + 0.5 * dt * k1)
        k3 = self.derivative(theta + 0.5 * dt * k2)
        k4 = self.derivative(theta + dt * k3)
        
        # Update phases
        self.phases = theta + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Add noise if specified
        if self.noise_std > 0:
            self.phases += np.random.normal(0, self.noise_std * np.sqrt(dt), self.N)
            
        # Keep phases within [0, 2π] for cleanliness (optional, math works without it)
        # self.phases = np.mod(self.phases, 2 * np.pi)
        
        return self.phases
