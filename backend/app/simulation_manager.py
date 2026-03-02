import numpy as np
from backend.src.model.dynamics import KuramotoNetwork
from backend.src.model.connectivity import generate_brain_network
from backend.src.metrics.synchronization import phase_coherence_magnitude
from backend.src.data.synthetic_eeg import RealisticEEGGenerator, phases_to_eeg
from backend.src.metrics.clinical import ClinicalMonitor
from backend.src.metrics.clinical_engine import ClinicalAnalysisEngine
from backend.src.reports.generator import ClinicalReportGenerator

class SimulationManager:
    """
    Manages the lifecycle of the Neuro-Computational simulation.
    Bridges the raw mathematical model with the API layer.
    """
    def __init__(self):
        self.is_running = False
        self.N = 20 # Channels
        self.dt = 0.005 # 200 Hz Sampling Rate (Required for 35Hz Filter)
        self.model = None
        self.monitor = ClinicalMonitor(sample_rate=int(1/self.dt))
        self.clinical_engine = ClinicalAnalysisEngine(fs=int(1/self.dt))
        self.eeg_generator = RealisticEEGGenerator(N=self.N, fs=int(1/self.dt))
        
        # Reporting
        self.report_generator = ClinicalReportGenerator()
        self.event_log = [] # Persistent log for report
        self.pending_report = None
        
        self.reset_simulation()
        
    def reset_simulation(self):
        """Re-initializes the model with fresh parameters."""
        adj = generate_brain_network(self.N, method='small_world', k=4, p=0.2)
        freqs = np.random.normal(10.0, 1.0, self.N)
        # Start in Normal state
        self.model = KuramotoNetwork(self.N, freqs, adj, coupling_strength=0.5, dt=self.dt, noise_std=0.5)
        self.monitor = ClinicalMonitor(sample_rate=int(1/self.dt)) # Reset Clinical State
        self.clinical_engine = ClinicalAnalysisEngine(fs=int(1/self.dt)) # Reset Analysis State
        self.event_log = []
        self.iteration = 0
    
    def handle_command(self, command: dict):
        """Process control commands from the frontend."""
        action = command.get("action")
        payload = command.get("payload", {})
        
        if action == "START":
            self.is_running = True
        elif action == "STOP":
            self.is_running = False
        elif action == "RESET":
            self.reset_simulation()
            self.is_running = False
        elif action == "SET_PARAM":
            param = payload.get("param")
            value = payload.get("value")
            if param == "coupling":
                # User manually adjusting K
                self.model.K = float(value)
        elif action == "TRIGGER_SEIZURE":
            self.model.K = 8.0 # Hypersynchrony
        elif action == "TRIGGER_NORMAL":
            self.model.K = 0.5 # Normal
        elif action == "TRIGGER_SUPPRESSION":
            self.model.K = 0.1 # Suppression
        elif action == "TOGGLE_EYES":
            # Toggle Generator State
            self.eeg_generator.eyes_closed = not self.eeg_generator.eyes_closed
        elif action == "INJECT_SPIKE":
            # Inject into random or specific channel
            # Default to random for button click
            import random
            ch = random.randint(0, self.N - 1)
            self.eeg_generator.trigger_spike(ch)
            self.event_log.append({"type": "SPIKE", "t": self.iteration * self.dt, "desc": "Manual Spike Injection"})
        elif action == "TRIGGER_BLINK":
            self.eeg_generator.trigger_blink()
            # Send System Event to Frontend
            self.last_trigger = {"type": "BLINK_MARK", "t": self.iteration * self.dt}
            self.event_log.append({"type": "ARTIFACT", "t": self.iteration * self.dt, "desc": "Blink Artifact"})
        elif action == "TOGGLE_ARTIFACTS":
            # Toggle Artifacts
            self.eeg_generator.artifacts_enabled = not self.eeg_generator.artifacts_enabled
        elif action == "TOGGLE_ICA":
            # Toggle ICA Filter
            self.eeg_generator.ica_enabled = not self.eeg_generator.ica_enabled
        elif action == "GENERATE_REPORT":
            # Generate Report
            # We need current state. We'll capture it in next step or use cached
            # Ideally we pass current metrics. 
            self.request_report_generation = True # Flag for step loop
            
    def step(self):
        """Advances the simulation one step and returns the state."""
        if not self.model:
            return {}
            
        phases = self.model.step()
        voltages = self.eeg_generator.generate_step(phases, self.model.K)
        
        order_param = phase_coherence_magnitude(phases)
        self.iteration += 1
        
        # Clinical Monitoring (Global Metrics)
        clinical_state = self.monitor.update(voltages)
        
        # Clinical Analysis (Spectral & Morphology)
        analysis_results = self.clinical_engine.update(voltages, timestamp=self.iteration * self.dt)
        
        # Auto-log detected events
        if analysis_results.get("events"):
            for evt in analysis_results["events"]:
                self.event_log.append(evt)
        
        # Inject Manual Events (Blink Markers)
        if hasattr(self, 'last_trigger') and self.last_trigger:
            if "events" not in analysis_results: analysis_results["events"] = []
            analysis_results["events"].append({
                "type": self.last_trigger["type"],
                "channel": "SYS", # System Channel
                "time": self.last_trigger["t"],
                "confidence": 1.0,
                "desc": "User Triggered Event"
            })
            self.last_trigger = None
            
        # Add Context Metadata (Eyes, Artifacts)
        analysis_results["meta"] = {
            "eyes": "CLOSED" if self.eeg_generator.eyes_closed else "OPEN",
            "artifacts": "ON" if self.eeg_generator.artifacts_enabled else "OFF"
        }
        
        # --- FUNCTIONAL CONNECTIVITY ANALYSIS ---
        # Identify strongly synchronized pairs (Phase Locking Value proxy)
        # We calculate phase difference between all pairs.
        # High "connection" if phase difference is near 0.
        links = []
        # Optimization: Only check a subset or top N? 
        # Let's do a quick naive N^2 check (N=20 is small)
        for i in range(self.N):
            for j in range(i + 1, self.N):
                # Phase diff
                diff = np.abs(phases[i] - phases[j])
                # Wrap to 0-pi
                if diff > np.pi: diff = 2*np.pi - diff
                
                # Coherence metric: 1.0 - (diff / pi)
                coherence = 1.0 - (diff / np.pi)
                
                if coherence > 0.85: # Threshold for "Active Link"
                    links.append({
                        "source": self.eeg_generator.channel_names[i] if hasattr(self.eeg_generator, 'channel_names') else f"Ch{i}",
                        "target": self.eeg_generator.channel_names[j] if hasattr(self.eeg_generator, 'channel_names') else f"Ch{j}",
                        "strength": float(coherence),
                        "s_idx": i,
                        "t_idx": j
                    })
        
        # Sort by strength and take top 10 to avoid visual clutter
        links.sort(key=lambda x: x['strength'], reverse=True)
        analysis_results["connectivity"] = links[:12]
        
        # Determine status text locally (simple logic)
        status = "NORMAL"
        if self.model.K > 4.0:
            status = "SEIZURE"
        elif self.model.K < 0.2:
            status = "SUPPRESSED"
            
        # Report Generation Logic
        report_data = None
        if hasattr(self, 'request_report_generation') and self.request_report_generation:
            metrics_dict = {
                "order_parameter": float(order_param),
                "coupling_strength": float(self.model.K),
                "bsr": float(clinical_state["bsr"]),
                "metabolic_reserve": float(clinical_state["metabolic_reserve"])
            }
            report_text = self.report_generator.generate(metrics_dict, analysis_results, self.event_log)
            report_data = report_text
            self.request_report_generation = False
            
        return {
            "timestamp": self.iteration * self.dt,
            "eeg": voltages.tolist(),
            "metrics": {
                "order_parameter": float(order_param),
                "coupling_strength": float(self.model.K),
                "bsr": float(clinical_state["bsr"]),
                "metabolic_reserve": float(clinical_state["metabolic_reserve"]),
                "clinical_decision": clinical_state["decision"],
                "alert_level": clinical_state["alert_level"]
            },
            "analysis": analysis_results, 
            "status": status,
            "report": report_data # Sent only when requested
        }
