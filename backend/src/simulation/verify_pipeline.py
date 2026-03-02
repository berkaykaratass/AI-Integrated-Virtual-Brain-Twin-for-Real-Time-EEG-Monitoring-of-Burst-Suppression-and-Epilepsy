import numpy as np
import matplotlib.pyplot as plt
from backend.src.data.synthetic_eeg import generate_synthetic_eeg_from_model
from backend.src.model.connectivity import generate_brain_network
from backend.src.model.dynamics import KuramotoNetwork
from backend.src.metrics.signal_processing import extract_instantaneous_phase, bandpass_filter

def verify_signal_pipeline():
    # 1. Setup Model
    N = 5
    duration = 2.0
    fs = 250.0 # Hz
    
    adj = generate_brain_network(N)
    freqs = np.array([10.0] * N) # 10 rad/s approx 1.6 Hz, let's bump to 10 Hz
    freqs = np.array([2 * np.pi * 10.0] * N) # 10 Hz
    
    model = KuramotoNetwork(N, freqs, adj, coupling_strength=0.1, dt=1/fs)
    
    # 2. Generate Data
    print("Generating Synthetic EEG...")
    data = generate_synthetic_eeg_from_model(model, duration, fs)
    eeg = data['eeg'] # [N, Time]
    true_phases = data['true_phases']
    time = data['time']
    
    # 3. Process Data (Pipeline Test)
    # A. Filter (Alpha band 8-12 Hz)
    print("Applying Bandpass Filter (8-12 Hz)...")
    filtered_eeg = bandpass_filter(eeg, 8, 12, fs, order=4)
    
    # B. Hilbert Transform
    print("Extracting Phase via Hilbert...")
    estimated_phases = extract_instantaneous_phase(filtered_eeg)
    
    # 4. Compare Ground Truth vs Estimated
    # Phase is cyclic [-pi, pi], so we compare difference modulo 2pi
    # But Hilbert gives phase of the *signal*, while Kuramoto has intrinsic phase. 
    # V = cos(theta). Hilbert(V) -> should recover theta (wrapped).
    
    # Select channel 0
    ch = 0
    theta_true = np.mod(true_phases[ch], 2*np.pi)
    # Hilbert gives [-pi, pi], map to [0, 2pi] for comparison
    theta_est = np.mod(estimated_phases[ch], 2*np.pi)
    
    # Verification Plot
    plt.figure(figsize=(10, 6))
    
    plt.subplot(3, 1, 1)
    plt.plot(time, eeg[ch], label='Raw Synthetic EEG', alpha=0.5)
    plt.plot(time, filtered_eeg[ch], label='Filtered (8-12Hz)', color='black', lw=1)
    plt.title('Signal Filtering')
    plt.legend()
    
    plt.subplot(3, 1, 2)
    plt.plot(time, theta_true, label='True Model Phase', linestyle='None', marker='.', markersize=2)
    plt.plot(time, theta_est, label='Hilbert Estimated Phase', alpha=0.7)
    plt.title('Phase Reconstruction Verification')
    plt.legend()
    
    plt.subplot(3, 1, 3)
    error = np.abs(np.exp(1j*theta_true) - np.exp(1j*theta_est)) # Complex distance
    plt.plot(time, error, color='red')
    plt.title('Phase Error (Complex Distance)')
    plt.ylim(0, 2)
    
    plt.tight_layout()
    plt.savefig('pipeline_verification.png')
    print("Verification plot saved to pipeline_verification.png")

if __name__ == "__main__":
    verify_signal_pipeline()
