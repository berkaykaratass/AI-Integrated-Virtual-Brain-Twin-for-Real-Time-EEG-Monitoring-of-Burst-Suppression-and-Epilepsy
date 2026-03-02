import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi

class AnalogFilter:
    """
    Stateful IIR filter to mimic analog EEG amplifiers (Bandpass 0.5 - 35 Hz).
    Removes 'digital' step artifacts and smooths transitions.
    """
    def __init__(self, N, fs=200.0, low=0.5, high=30.0):
        self.N = N
        self.fs = fs
        nyq = 0.5 * fs
        # 2nd order Butterworth bandpass
        self.b, self.a = butter(2, [low/nyq, high/nyq], btype='band')
        # Initialize filter state (zi) for each channel to avoid transients
        self.zi = np.zeros((N, len(self.a) - 1))
        
    def process(self, raw_samples):
        """
        Filters a chunk of samples (or single sample step) maintaining state.
        raw_samples: shape (N,)
        """
        filtered = np.zeros_like(raw_samples)
        # Filter channel by channel (scipy lfilter is stateful via zi)
        for i in range(self.N):
            out, self.zi[i] = lfilter(self.b, self.a, [raw_samples[i]], zi=self.zi[i])
            filtered[i] = out[0]
        return filtered

class RealisticEEGGenerator:
    """
    Generates 'Textbook Level' realistic EEG signals.
    v2: Uses Pink Noise + Filtering for non-digital look.
    """
    def __init__(self, N=20, fs=200.0):
        self.N = N
        self.fs = fs
        self.t = 0
        
        # State vectors for Burst-Suppression (0=Suppression, 1=Burst)
        self.bs_state = np.zeros(N) 
        self.burst_timers = np.zeros(N)
        
        # Physics Engines
        self.filter = AnalogFilter(N, fs)
        
        # Pink Noise State (One state per channel)
        self.pink_state = np.random.randn(N, 16) # Multiple poles for pink noise approx
        
        # 10-20 Configuration
        self.hemispheres = np.array([0]*10 + [1]*10) # 0=Left, 1=Right
        self.posterior_channels = [6, 7, 9, 15, 16, 17, 19] # P3, O1, Pz, T6, P4, O2, Oz (approx)
        
        # Clinical States
        self.eyes_closed = True # Default: Relaxed Alpha
        self.artifacts_enabled = True # Source of artifacts
        self.ica_enabled = False # ICA Filter State
        self.spike_queue = [] # Queue for on-demand spikes: [(channel_idx, duration_left)]
        self.blink_active = False
        self.blink_timer = 0
        
    def trigger_blink(self):
        """Simulate an eye blink (Frontal delta wave)"""
        if not self.artifacts_enabled: return
        self.blink_active = True
        self.blink_timer = int(0.4 * self.fs) # 400ms blink

    def _generate_pink_noise(self):
        """McCartney's algorithm for 1/f noise (approx)"""
        white = np.random.randn(self.N) * 1.0
        # Simple IIR approx for pinking
        # (Simplified for real-time per-sample)
        # We'll stick to a simpler "Brownian-ish" walk with leak for stability
        # New sample = 0.95 * old + white
        self.pink_state[:, 0] = 0.95 * self.pink_state[:, 0] + white * 0.5
        return self.pink_state[:, 0]

    def _update_bs_dynamics(self, bsr_target=0.7):
        """Stochastic State Machine for Burst-Suppression"""
        for i in range(self.N):
            self.burst_timers[i] -= 1
            if self.burst_timers[i] <= 0:
                if self.bs_state[i] == 0: # Suppressed -> Burst?
                    if np.random.random() > bsr_target: 
                        self.bs_state[i] = 1 
                        duration = np.random.uniform(0.5, 3.0) # Burst 0.5-3s
                        self.burst_timers[i] = int(duration * self.fs)
                    else:
                        self.burst_timers[i] = int(np.random.uniform(1.0, 5.0) * self.fs)
                else: # Burst -> Suppressed
                    self.bs_state[i] = 0 
                    duration = np.random.uniform(2.0, 10.0) # Suppress 2-10s
                    self.burst_timers[i] = int(duration * self.fs)

    def generate_step(self, kuramoto_phases: np.ndarray, coupling_strength: float) -> np.ndarray:
        self.t += 1.0/self.fs
        
        # 1. Base Signal Source: PINK NOISE (Not Sine Waves)
        # This gives the "irregular" look naturally
        raw_noise = self._generate_pink_noise()
        
        # 2. Determine States
        target_signal = np.zeros(self.N)
        
        if coupling_strength < 0.4: # --- BURST SUPPRESSION ---
            target_bsr = np.clip(1.0 - (coupling_strength * 2.5), 0.2, 0.98)
            self._update_bs_dynamics(target_bsr)
            
            for i in range(self.N):
                if self.bs_state[i] == 1:
                    # BURST: High Amplitude chaotic waves
                    # Mix of Delta (1-4Hz) and sharp transients
                    delta = np.sin(2 * np.pi * 2.0 * self.t + i) * 30
                    sharp = np.random.randn() * 10 * (np.random.random() > 0.9) # Occasional spikes
                    
                    target_signal[i] = (raw_noise[i] * 40) + delta + sharp
                else:
                    # SUPPRESSION: Isoelectric (<5 uV)
                    # Reduced noise floor to ensure BSR threshold (5uV) is not breached by noise alone
                    target_signal[i] = np.random.normal(0, 0.5) 
                    
        elif coupling_strength > 6.0: # --- SEIZURE ---
            # Hypersynchronous Spike-Wave
            spike = np.power(np.sin(2 * np.pi * 3.0 * self.t), 3) * 150
            target_signal = spike + (raw_noise * 10)
            
        else: # --- NORMAL ---
            # Posterior Dominance: Alpha is strongest in Occipital/Parietal regions.
            
            alpha_power = 0.0
            if self.eyes_closed:
                alpha_power = 30.0 
            else:
                alpha_power = 5.0 
            
            # --- REALISM FIX 1: Harmonic Distortion (No perfect sine) ---
            # Add 2nd H (20Hz) and small randomness to frequency
            t_jitter = self.t + (np.random.normal(0, 0.005)) # Phase jitter
            alpha_wave = np.sin(2 * np.pi * 10.0 * t_jitter) 
            alpha_wave += 0.15 * np.sin(2 * np.pi * 20.0 * t_jitter + np.pi/4) # 2nd Harmonic
            
            for i in range(self.N):
                # --- REALISM FIX 2: Spatial Heterogeneity (Amplitude Gradients) ---
                # Not all channels are equal.
                ch_gain = 1.0
                
                # Topological variations
                if i in self.posterior_channels: 
                    ch_gain *= 1.8 # Occipital is LOUD for Alpha
                elif i in [0, 10]: # Fp1, Fp2
                    ch_gain *= 0.8 # Frontal often lower amplitude for alpha (but catches eye drift)
                elif i in [3, 13]: # T3, T4 (Temporal)
                    ch_gain *= 0.9 # Thicker bone/muscle?
                
                # Random biological variance (Fixed per channel at init ideally, but simplified here)
                # We'll stick to functional gain.
                
                # --- REALISM FIX 3: Phase Conduction Delay ---
                # Anterior channels lag slightly behind Posterior for Alpha? 
                # Or just random slight offsets to break "vertical line" sync
                # We simply don't just add alpha_wave directly.
                
                # Phase offset based on channel index to simulate travel
                local_wave = np.sin(2 * np.pi * 10.0 * (t_jitter - (i * 0.002))) 
                local_wave += 0.15 * np.sin(2 * np.pi * 20.0 * (t_jitter - (i * 0.002)) + np.pi/4)
                
                # Compose Signal
                # Pink noise is the "texture"
                # Alpha is the "rhythm"
                
                pwr = alpha_power * ch_gain
                
                # Add natural amplitude fluctuations (Waxing/Waning)
                # 0.1Hz modulation
                envelope = 0.8 + 0.4 * np.sin(2 * np.pi * 0.1 * self.t + i)
                
                target_signal[i] = (raw_noise[i] * 12) + (local_wave * pwr * envelope)

        # 3. Artifact Injection (Before Filter)
        # In a real ICA, we would separate mixed signals. Here we have ground truth.
        # "ICA Cleaning" means we reconstruct the signal WITHOUT the artifact components.
        
        drift = 0
        line = 0
        blink_val = 0
        
        # Calculate Artifact Components (Always calc them to maintain state/timers)
        if self.artifacts_enabled:
            # Baseline Drift (Reduced to prevent masking suppression)
            drift = 4.0 * np.sin(2 * np.pi * 0.2 * self.t + np.linspace(0, 6, self.N))
            # 50 Hz Line Noise
            line = 1.0 * np.sin(2 * np.pi * 50.0 * self.t)
            
            # BLINK ARTIFACT (Time-Locked)
            if self.blink_active:
                self.blink_timer -= 1
                if self.blink_timer <= 0: self.blink_active = False
                # Bell curve shape (Gaussian)
                width = 20.0
                x = (200 - self.blink_timer) / width 
                # Centered Gaussian
                blink_val = 300.0 * np.exp(-(x - 2.5)**2 / 2.0)

        # Apply artifacts UNLESS ICA is active
        # ICA removes "Eye Blink" and "Line Noise" components
        if not self.ica_enabled:
            total_raw = target_signal + drift + line
            
            if blink_val > 0.1:
                # Apply Blink to Frontal Channels (Fp1, Fp2) - Indices 0, 10
                total_raw[0] += blink_val
                total_raw[10] += blink_val
                # Bleed into F7/F8 (1, 11) less
                total_raw[1] += blink_val * 0.3
                total_raw[11] += blink_val * 0.3
        else:
            # ICA ENABLED: Pure Signal (Simulating perfect component rejection)
            total_raw = target_signal

        # 4. Spike Injection (On Demand)
        # --- ON-DEMAND API SPIKE INJECTION ---
        # User pressed "Inject Spike"
        # We handle the queue: list of objects { 'ch': int, 't': int }
        # Simplified: self.spike_queue is list of channel indices to spike NOW
        
        return self._process_injections_and_filter(total_raw)
        
    def trigger_spike(self, channel_index: int):
        """External API calls this"""
        self.spike_queue.append(channel_index)

    def _process_injections_and_filter(self, target_signal: np.ndarray):
        # Handle Spike Queue -> Transfer to active timers
        # We'll use self.burst_timers for simplicity or a new one? 
        # Let's stick to the current flow. We need a new state for "Injected Spike"
        # But we can just add it to the signal before filtering.
        
        scale = 200.0 # uV
        
        # Process queue
        while self.spike_queue:
            ch = self.spike_queue.pop(0)
            # We create a simplified "impulse" that the filter will shape into a spike?
            # Or we add a deterministic waveform.
            # Let's add a deterministic "Spike" waveform over next few samples?
            # Since this is sample-by-sample, we need state.
            # Let's cheat: Add a huge value NOW and let the filter ring?
            # Better: Add to a "spike_active" buffer.
            pass 
            # (See below for implementation in next step)
            
        # RE-IMPLEMENTING PROPERLY:
        # We need a `generated_spikes` buffer that decays.
        if not hasattr(self, 'spike_envelope'):
             self.spike_envelope = np.zeros(self.N)
             
        # Check queue
        while self.spike_queue:
            ch = self.spike_queue.pop(0)
            self.spike_envelope[ch] = 1.0 # Start spike
            
        # Decay envelope and add shape
        for i in range(self.N):
            if self.spike_envelope[i] > 0.01:
                # Morph: Sharp rise, slow fall
                # Current simple mechanics:
                target_signal[i] -= (self.spike_envelope[i] * 300.0) # Downward spike (standard EEG convention often negative up, but here we just do neg voltage)
                self.spike_envelope[i] *= 0.85 # Fast decay (approx 50ms)
            else:
                self.spike_envelope[i] = 0.0

        # ... (Artifacts)
        # Baseline Drift
        drift = 10 * np.sin(2 * np.pi * 0.2 * self.t + np.linspace(0, 6, self.N))
        line = 3.0 * np.sin(2 * np.pi * 50.0 * self.t)
        
        total_raw = target_signal + drift + line
        return self.filter.process(total_raw)


def phases_to_eeg(phases: np.ndarray, amplitudes: np.ndarray = None) -> np.ndarray:
    return np.cos(phases)
