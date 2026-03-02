import numpy as np
from collections import deque

class ClinicalMonitor:
    def __init__(self, sample_rate=200, window_seconds=10):
        self.fs = sample_rate
        self.window_size = int(window_seconds * sample_rate)
        # BSR parameters
        self.energy_history = deque(maxlen=self.window_size)
        self.suppression_threshold = 5.0 # uV RMS (Noise floor is ~2-3uV)
        
        # Metabolic Model Parameters
        # Reserve starts at 1.0 (100%). 
        # Suppression recovers reserve (rest), but TOO MUCH suppression might imply drug toxicity (separate model).
        # Here we model "Synaptic Fatigue" from active bursting.
        # But per user request: "Iatrogenic risk = excessive inhibition".
        # So we model "Metabolic Viability":
        # - Healthy activity maintains homeostasis.
        # - Seizure (High activity) depletes reserve fast (Excitotoxicity).
        # - Deep Suppression (Zero activity) also depletes reserve slowly (Metabolic failure/hypothermia analogy or drug toxicity).
        self.metabolic_reserve = 1.0 
        self.recovery_rate = 0.001
        self.depletion_rate_seizure = 0.005
        self.depletion_rate_suppression = 0.0005 # Slow toxicity accumulation
        
    def update(self, eeg_data: np.ndarray) -> dict:
        """
        Updates clinical state with new EEG frame.
        eeg_data: shape (n_channels, n_time_points) or (n_channels,)
        """
        # 1. Calculate Instantaneous Energy (RMS across channels)
        if eeg_data.ndim > 1:
            frame_energy = np.mean(np.sqrt(np.mean(eeg_data**2, axis=0)))
        else:
            frame_energy = np.sqrt(np.mean(eeg_data**2))
            
        self.energy_history.append(frame_energy)
        
        # 2. Calculate BSR (Burst Suppression Ratio)
        # Ratio of time points in history below threshold
        if len(self.energy_history) == self.energy_history.maxlen:
            history_arr = np.array(self.energy_history)
            # Dynamic thresholding could be better, but fixed for now
            # Assume calibrated signal
            suppressed_points = np.sum(history_arr < self.suppression_threshold)
            bsr = suppressed_points / len(history_arr)
        else:
            bsr = 0.0
            
        # 3. Update Metabolic/Risk Model
        # Define states based on global energy
        if frame_energy > 40.0: # Seizure / High Burst (Normal Alpha is ~25uV)
            self.metabolic_reserve -= self.depletion_rate_seizure
        elif frame_energy < self.suppression_threshold: # Suppression (< 5uV)
            # In clinical B-S context, suppression is therapeutic up to a point, then toxic.
            # We assume continuous administration of propofol/barbiturates depletes "drug safety margin"
            self.metabolic_reserve -= self.depletion_rate_suppression
        else: # Normal / Healthy activity (5uV - 40uV)
            self.metabolic_reserve += self.recovery_rate
            
        # Clamp
        self.metabolic_reserve = max(0.0, min(1.0, self.metabolic_reserve))
        
        # 4. Clinical Decision
        decision = "MONITORING"
        alert_level = "GREEN"
        
        if bsr > 0.8:
            decision = "DECREASE DOSE (Toxic)"
            alert_level = "RED"
        elif 0.5 <= bsr <= 0.8:
            decision = "MAINTAIN (Therapeutic)"
            alert_level = "GREEN"
        elif 0.1 < bsr < 0.5:
             decision = "INCREASE DOSE (Sub-therapeutic)"
             alert_level = "YELLOW"
        else:
             if self.metabolic_reserve < 0.3:
                 decision = "CRITICAL: EXHAUSTION"
                 alert_level = "RED"
        
        return {
            "bsr": bsr,
            "metabolic_reserve": self.metabolic_reserve,
            "decision": decision,
            "alert_level": alert_level,
            "energy": frame_energy
        }
