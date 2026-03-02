import numpy as np
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ClinicalEvent:
    timestamp: float
    channel_index: int
    channel_name: str
    event_type: str # "SPIKE", "SHARP_WAVE", "BURST", "SUPPRESSION", "ARTIFACT"
    confidence: float
    description: str

class ClinicalAnalysisEngine:
    """
    Real-time Clinical EEG Analysis Engine.
    Performs Spectral Analysis (Band Power) and Morphological Pattern Detection.
    """
    def __init__(self, fs: float = 200.0):
        self.fs = fs
        self.channel_names = [
            'Fp1', 'F7', 'F3', 'T3', 'C3', 'T5', 'P3', 'O1', 'Fz', 'Pz',
            'Fp2', 'F8', 'F4', 'T4', 'C4', 'T6', 'P4', 'O2', 'Cz', 'Oz'
        ]
        
        # Frequency Bands
        self.bands = {
            'Delta': (0.5, 4),
            'Theta': (4, 8),
            'Alpha': (8, 13),
            'Beta': (13, 30),
            'Gamma': (30, 45)
        }
        
        # Buffers for spectral analysis (need ~1-2 sec of data for decent resolution)
        self.buffer_size = int(2.0 * fs) 
        self.eeg_buffer = np.zeros((20, self.buffer_size))
        
    def update(self, new_samples: np.ndarray, timestamp: float) -> Dict:
        """
        Process new chunk of data [Channels, Samples] or [Channels] (single step)
        """
        # 1. Update Buffer (Rolling)
        # Assuming new_samples is (20,) for single step or (20, N)
        if new_samples.ndim == 1:
            new_samples = new_samples[:, np.newaxis]
            
        n_new = new_samples.shape[1]
        self.eeg_buffer = np.roll(self.eeg_buffer, -n_new, axis=1)
        self.eeg_buffer[:, -n_new:] = new_samples
        
        # 2. Analyze
        spectral_data = self._compute_spectral_power()
        events = self._detect_patterns(new_samples[:, -1], timestamp) 
        bg_class = self._classify_background(spectral_data)
        
        # Topographic Ratios (Artifact Verification)
        # Anterior: Fp1, Fp2 (0, 10). Posterior: O1, O2 (7, 17)
        ant_amp = np.mean(np.abs(self.eeg_buffer[[0, 10], -50:])) # last 250ms
        post_amp = np.mean(np.abs(self.eeg_buffer[[7, 17], -50:]))
        ap_ratio = ant_amp / (post_amp + 0.1)
        
        return {
            "spectral": spectral_data,
            "events": events,
            "background": bg_class,
            "ratios": { "ant_post": float(ap_ratio) }
        }
    
    def _classify_background(self, spectral) -> str:
        """
        Heuristic classification of background rhythm.
        """
        # Get mean global powers
        delta = np.mean(spectral['Delta'])
        alpha = np.mean(spectral['Alpha'])
        
        # Avoid div by zero
        if delta + alpha < 1.0: return "SUPPRESSED / ISOELECTRIC"
        
        ratio = delta / (alpha + 0.1)
        
        if delta < 5.0 and alpha < 5.0:
            return "LOW VOLTAGE / SUPPRESSED"
            
        if ratio > 3.0:
            return "DIFFUSE SLOWING (DELTA)"
        elif alpha > delta:
            return "NORMAL (ALPHA DOMINANT)"
        else:
            return "MIXED FREQUENCY"
        
    def _compute_spectral_power(self) -> Dict[str, np.ndarray]:
        """Simple FFT-based band power estimation on the buffer"""
        # Apply windowing
        window = np.hanning(self.buffer_size)
        windowed = self.eeg_buffer * window
        
        # FFT
        fft_vals = np.fft.rfft(windowed, axis=1)
        psd = np.abs(fft_vals)**2
        freqs = np.fft.rfftfreq(self.buffer_size, 1.0/self.fs)
        
        powers = {}
        for band_name, (low, high) in self.bands.items():
            idx = np.logical_and(freqs >= low, freqs <= high)
            if np.any(idx):
                # Mean power in band per channel
                powers[band_name] = np.mean(psd[:, idx], axis=1).tolist()
            else:
                powers[band_name] = [0.0] * 20
                
        return powers

    def _detect_patterns(self, latest_sample: np.ndarray, timestamp: float) -> List[Dict]:
        """
        Real-time time-domain morphology check.
        Look for Spikes, Sharp Waves, and Burst/Suppression status.
        Uses simple thresholding and derivatives since we are simulating.
        """
        events = []
        
        # We need a bit of history for morphology (derivative)
        # Look at last 100ms (20 samples)
        history = self.eeg_buffer[:, -20:]
        
        # Calculate derivatives (slope)
        diff1 = np.diff(history, axis=1) # Velocity
        diff2 = np.diff(diff1, axis=1)   # Acceleration (Sharpness)
        
        # Metrics for latest point
        # abs amplitude
        amp = np.abs(latest_sample)
        # max sharpness in recent window
        sharpness = np.max(np.abs(diff2), axis=1)
        
        for i in range(20):
            ch = self.channel_names[i]
            
            # 1. Artifact Detection (Clipping/Rail)
            if amp[i] > 150: # >150 uV is suspicious/artifact
                if amp[i] > 250:
                    events.append(self._make_event(timestamp, i, "ARTIFACT", 1.0, "High Amplitude Artifact"))
                continue # Skip other checks if artifact
            
            # 2. Spike Detection (High Sharpness + Moderate Amp)
            # Thresholds tuned for our realistic generator
            if sharpness[i] > 50 and amp[i] > 60:
                 events.append(self._make_event(timestamp, i, "SPIKE", 0.9, f"Epileptiform Spike at {ch}"))
                 
            # 3. Burst vs Suppression
            if amp[i] < 5.0: # Very strict < 5uV
                # Check if it has been low for a while (using buffer mean)
                recent_mean = np.mean(np.abs(self.eeg_buffer[i, -100:])) # last 500ms
                if recent_mean < 7.0:
                     # This is a continuous state, maybe don't emit event every step?
                     # Ideally handled by frontend state, but let's flag it.
                     pass 
        return events

    def _make_event(self, t, ch_idx, type, conf, desc):
        return {
            "time": t,
            "channel": self.channel_names[ch_idx],
            "type": type, # SPIKE, ARTIFACT
            "confidence": conf,
            "coord": {"x": 0, "y": 0}, # Placeholder, frontend maps this
            "desc": desc
        }
