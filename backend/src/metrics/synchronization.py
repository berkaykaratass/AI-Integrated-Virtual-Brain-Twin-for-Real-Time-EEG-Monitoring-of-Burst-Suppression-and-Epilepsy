import numpy as np

def global_order_parameter(phases: np.ndarray) -> complex:
    """
    Calculates the Kuramoto Global Order Parameter (R).
    
    R(t) = (1/N) * | Σ exp(i * θ_j(t)) |
    
    Args:
        phases (np.ndarray): 1D array of phases (theta) at a specific time step.
        
    Returns:
        complex: The complex order parameter. Its magnitude |z| is the order parameter R (0-1).
                 Its angle is the average phase.
    """
    if phases.size == 0:
        return 0.0
    
    z = np.mean(np.exp(1j * phases))
    return z

def phase_coherence_magnitude(phases: np.ndarray) -> float:
    """
    Returns the magnitude of the global order parameter (R).
    0 = Complete Incoherence (Random)
    1 = Complete Synchronization
    """
    z = global_order_parameter(phases)
    return np.abs(z)

def synchronization_entropy(phases: np.ndarray, bins: int = 18) -> float:
    """
    Calculates the Shannon entropy of the phase distribution.
    
    Args:
        phases (np.ndarray): Array of phases in [0, 2π].
        bins (int): Number of bins for histogram.
        
    Returns:
        float: Entropy value. Lower entropy means higher synchronization (peaked distribution).
               Si = - Σ p_k log(p_k)
    """
    # Ensure phases are in [0, 2π] range for histogram
    wrapped_phases = np.mod(phases, 2 * np.pi)
    
    counts, _ = np.histogram(wrapped_phases, bins=bins, range=(0, 2*np.pi), density=True)
    
    # Normalize probabilities
    # Note: 'density=True' returns value such that integral is 1. We want discrete prob sum=1.
    # So we prefer simple counts normalized.
    counts, _ = np.histogram(wrapped_phases, bins=bins, range=(0, 2*np.pi))
    p = counts / counts.sum()
    
    # Avoid log(0)
    p = p[p > 0]
    
    S = -np.sum(p * np.log(p))
    
    # Normalize by max entropy S_max = log(bins) to get range [0, 1] (optional)
    S_max = np.log(bins)
    return S / S_max
