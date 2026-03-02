import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from backend.src.model.dynamics import KuramotoNetwork
from backend.src.model.connectivity import generate_brain_network
from backend.src.metrics.synchronization import phase_coherence_magnitude
from backend.src.metrics.clinical import ClinicalMonitor
from backend.src.data.synthetic_eeg import phases_to_eeg, add_pink_noise

def run_clinical_dashboard():
    """
    Runs a real-time clinical dashboard simulation.
    Upper Panel: Multi-channel EEG Traces (scrolling)
    Lower Left: Phase Synchronization (Order Parameter Gauge)
    Lower Right: Clinical Status (Normal / Seizure / Suppression)
    """
    # Parameters
    N = 20 # Reduced channel count for visual clarity
    fs = 100.0
    dt = 1.0/fs
    buffer_size = 500 # 5 seconds window
    
    # Model Setup
    adj = generate_brain_network(N, method='small_world', k=4, p=0.2)
    freqs = np.random.normal(10.0, 1.0, N)
    model = KuramotoNetwork(N, freqs, adj, coupling_strength=0.5, dt=dt, noise_std=0.5)
    
    # State Variables
    eeg_buffer = np.zeros((N, buffer_size))
    time_points = np.linspace(-buffer_size*dt, 0, buffer_size)
    
    # Dynamics Controller
    iteration = [0]
    
    # Setup Plot
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2)
    
    # EEG Panel (Top, spans both cols)
    ax_eeg = fig.add_subplot(gs[0:2, :])
    lines = []
    offsets = np.arange(N) * 2.5 # Vertical spacing
    for i in range(N):
        line, = ax_eeg.plot(time_points, eeg_buffer[i] + offsets[i], color='black', lw=0.8)
        lines.append(line)
    
    ax_eeg.set_title("Real-time Multi-channel EEG Monitoring")
    ax_eeg.set_ylabel("Channels")
    ax_eeg.set_xlabel("Time (s)")
    ax_eeg.set_yticks([]) # Hide y ticks
    ax_eeg.set_xlim(time_points[0], time_points[-1])
    ax_eeg.set_ylim(-2, N*2.5 + 2)
    
    # Sync Gauge Panel (Bottom Left)
    ax_sync = fig.add_subplot(gs[2, 0])
    r_history = [0] * 100
    line_r, = ax_sync.plot(r_history, color='blue', lw=2)
    ax_sync.set_ylim(0, 1.1)
    ax_sync.set_title("Phase Synchronization (Order Parameter R)")
    ax_sync.set_ylabel("R")
    ax_sync.grid(True)
    
    # Status Alert Panel (Bottom Right)
    ax_status = fig.add_subplot(gs[2, 1])
    ax_status.axis('off')
    status_text = ax_status.text(0.5, 0.5, "NORMAL", ha='center', va='center', fontsize=24, weight='bold', 
                                 bbox=dict(facecolor='green', alpha=0.5, boxstyle='round'))
    
    def update(frame):
        t = iteration[0]
        iteration[0] += 1
        
        # Scenario Logic: Normal -> Seizure -> Burst Suppression -> Normal
        # 0-200: Normal (K=0.5)
        # 200-500: Seizure (K=8.0)
        # 500-800: Suppression (K=0.1)
        # 800+: Normal
        
        slow_t = t / 2.0 # Slow down transition for viz
        
        status = "NORMAL"
        color = "green"
        
        if 200 <= slow_t < 500:
            model.K = 8.0
            status = "SEIZURE DETECTED"
            color = "red"
        elif 500 <= slow_t < 800:
            model.K = 0.1
            status = "SUPPRESSION"
            color = "gray"
        else:
            model.K = 0.5
            
        # Step Model
        phases = model.step()
        
        # Generate EEG
        inst_vals = phases_to_eeg(phases)
        # Add noise per channel
        # Simple random addition
        inst_vals += np.random.normal(0, 0.1, N)
        
        # Roll buffer
        eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
        eeg_buffer[:, -1] = inst_vals
        
        # Calculate Metric
        r = phase_coherence_magnitude(phases)
        r_history.pop(0)
        r_history.append(r)
        
        # Update Plots
        for i, line in enumerate(lines):
            line.set_ydata(eeg_buffer[i] + offsets[i])
            
        line_r.set_ydata(r_history)
        
        # Update Text Status
        status_text.set_text(status)
        status_text.set_bbox(dict(facecolor=color, alpha=0.5, boxstyle='round'))
        
        return lines + [line_r, status_text]
    
    print("Starting Simulation Animation... (Close window to stop)")
    # Save a short clip instead of showing interactive window (since we are in headless env)
    ani = animation.FuncAnimation(fig, update, frames=1000, interval=20, blit=True)
    
    # Save as GIF or MP4
    writer = animation.PillowWriter(fps=30)
    ani.save("clinical_dashboard.gif", writer=writer)
    print("Dashboard saved to clinical_dashboard.gif")

if __name__ == "__main__":
    run_clinical_dashboard()
