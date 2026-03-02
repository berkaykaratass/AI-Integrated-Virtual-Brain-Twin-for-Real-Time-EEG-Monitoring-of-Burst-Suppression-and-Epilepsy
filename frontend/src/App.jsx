import React, { useEffect, useRef, useState } from 'react';
import Layout from './components/Layout';
import EEGCanvas from './components/EEGCanvas';
import BrainMRI from './components/BrainMRI';
import ClinicalPanel from './components/ClinicalPanel';
import SpectralDashboard from './components/SpectralDashboard';
import { Play, Square, Activity, Zap, Stethoscope, Brain } from 'lucide-react';

const WEBSOCKET_URL = "ws://localhost:8000/ws/simulation";

const Dashboard = () => {
    const [status, setStatus] = useState("DISCONNECTED");
    const [metrics, setMetrics] = useState({ r: 0, k: 0 });
    const [analysis, setAnalysis] = useState(null);
    const [montage, setMontage] = useState('REF');
    const [channels, setChannels] = useState([]); // Buffer for brain viz
    const [reportText, setReportText] = useState(null);
    const [showReport, setShowReport] = useState(false);
    const [icaEnabled, setIcaEnabled] = useState(false);

    // Playback State
    const [history, setHistory] = useState([]); // Array of { eeg, analysis, metrics, timestamp }
    const [isPaused, setIsPaused] = useState(false);
    const [playbackIndex, setPlaybackIndex] = useState(-1); // -1 = Live

    const wsRef = useRef(null);
    const dataRef = useRef({ queue: [] });

    useEffect(() => {
        const connect = () => {
            const ws = new WebSocket(WEBSOCKET_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("Connected to NeuroSync Core");
                setStatus("READY");
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                // Construct Frame for History
                const frame = {
                    timestamp: Date.now(),
                    eeg: data.eeg || null,
                    analysis: data.analysis || null,
                    metrics: data.metrics || null,
                    status: data.status || status
                };

                setHistory(prev => {
                    const newHistory = [...prev, frame];
                    if (newHistory.length > 5000) return newHistory.slice(-5000); // 25 sec buffer approx if 200Hz? No, WS sends packets.
                    // Packet rate is ? If 200Hz samples come in packs of 1, 5000 is 25s.
                    // If packs are bigger (e.g. 10 samples), 5000 is 250s.
                    return newHistory;
                });

                // LIVE MODE: Only update View if NOT paused
                if (!isPaused) {
                    if (data.eeg) {
                        dataRef.current.queue.push(data.eeg);
                        // Keep only latest frame for brain viz pulse
                        setChannels(data.eeg);
                    }
                    if (data.metrics) {
                        setMetrics({
                            ...data.metrics,
                            r: data.metrics.order_parameter?.toFixed(2) || "0.00",
                            k: data.metrics.coupling_strength?.toFixed(1) || "0.0"
                        });
                    }
                    if (data.analysis) {
                        setAnalysis(data.analysis);
                        if (data.analysis.meta && data.analysis.meta.artifacts === "OFF" && !icaEnabled) {
                            // Sync logic
                        }
                    }
                    if (data.report) {
                        setReportText(data.report);
                        setShowReport(true);
                    }
                    if (data.status) {
                        setStatus(data.status);
                    }
                }
            };

            ws.onclose = () => {
                console.log("Disconnected. Reconnecting...");
                setStatus("DISCONNECTED");
                setTimeout(connect, 3000);
            };
        };
        connect();

        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const sendCommand = (action, payload = {}) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ action, payload }));
        }
    };

    const toggleICA = () => {
        setIcaEnabled(!icaEnabled);
        sendCommand("TOGGLE_ICA");
    };

    // Playback Logic
    const handleScrub = (e) => {
        const idx = parseInt(e.target.value);
        setPlaybackIndex(idx);
        setIsPaused(true);

        // Update View to Historical Frame
        const frame = history[idx];
        if (frame) {
            // Brain Viz
            if (frame.eeg) setChannels(frame.eeg);

            // Metrics
            if (frame.metrics) setMetrics({
                ...frame.metrics,
                r: frame.metrics.order_parameter?.toFixed(2),
                k: frame.metrics.coupling_strength?.toFixed(1)
            });

            // Analysis (Spectral)
            if (frame.analysis) setAnalysis(frame.analysis);

            // Status
            if (frame.status) setStatus(frame.status);
        }
    };

    const handleResume = () => {
        setIsPaused(false);
        setPlaybackIndex(-1);
        // Clear canvas playback mode implicitly by passing null
    };

    // Prepare Playback Data for Canvas
    // EEGCanvas needs [ [ch0 stores], [ch1 stores] ]
    // History is [ {eeg: [v0...v19]}, ... ]
    // We need to slice history around playbackIndex to fill the screen
    // Let's take 500 frames before playbackIndex
    const getCanvasPlaybackData = () => {
        if (!isPaused || playbackIndex < 0) return null;

        const windowSize = 400; // frames
        const start = Math.max(0, playbackIndex - windowSize);
        const sl = history.slice(start, playbackIndex + 1);

        // Convert to Channel-Major
        const buffer = Array(20).fill().map(() => []);
        sl.forEach(fr => {
            if (fr.eeg) {
                fr.eeg.forEach((val, ch) => {
                    buffer[ch].push(val);
                });
            }
        });
        return buffer;
    }

    const playbackData = getCanvasPlaybackData();

    // Activity level 
    const activityLevel = parseFloat(metrics.r) || 0;

    return (
        <Layout status={status}>
            <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] max-h-[calc(100vh-4rem)] overflow-hidden bg-medical-bg">

                {/* TIMELINE SLIDER (New) */}
                <div className="h-14 bg-medical-panel border-b border-medical-surface flex items-center px-6 gap-4 z-20 shrink-0">
                    <button
                        onClick={() => isPaused ? handleResume() : setIsPaused(true)}
                        className={`w-10 h-10 flex items-center justify-center rounded-full ${isPaused ? 'bg-green-500 hover:bg-green-600' : 'bg-yellow-500 hover:bg-yellow-600'} text-white shadow-lg transition-all`}
                    >
                        {isPaused ? <Play className="w-4 h-4 fill-current" /> : <div className="w-3 h-3 border-l-4 border-r-4 border-white h-4"></div>}
                    </button>

                    <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-medical-muted tracking-wider">
                            {isPaused ? "PLAYBACK PAUSED" : "LIVE MONITORING"}
                        </span>
                        <span className="text-xs font-mono text-cyan-400">
                            {isPaused ? `Frame: ${playbackIndex}` : "Real-time"}
                        </span>
                    </div>

                    <div className="flex-1 flex items-center gap-2">
                        <span className="text-[10px] text-slate-500">T-5m</span>
                        <input
                            type="range"
                            min="0"
                            max={Math.max(0, history.length - 1)}
                            value={isPaused && playbackIndex !== -1 ? playbackIndex : Math.max(0, history.length - 1)}
                            onChange={handleScrub}
                            className="flex-1 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 border border-slate-700"
                            disabled={history.length === 0}
                        />
                        <span className="text-[10px] text-slate-500">NOW</span>
                    </div>
                </div>

                <div className="flex-1 p-4 lg:p-6 grid grid-cols-12 gap-6 overflow-hidden">

                    {/* Left Column: Controls & Brain Viz */}
                    <div className="col-span-12 lg:col-span-4 flex flex-col gap-6 h-full overflow-y-auto pr-2">

                        {/* Status Card */}
                        <div className="bg-medical-panel rounded-xl border border-medical-surface p-5 shadow-medical flex items-center justify-between">
                            <div>
                                <h2 className="text-sm font-bold text-medical-muted uppercase tracking-wider mb-1">CORTEX STATUS</h2>
                                <div className={`text-2xl font-bold font-mono py-1 px-3 rounded-md inline-block ${status === 'SEIZURE' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                                    {status}
                                </div>
                            </div>
                            <Activity className={`w-8 h-8 ${status === 'SEIZURE' ? 'text-red-500 animate-pulse' : 'text-green-500'}`} />
                        </div>

                        {/* Clinical Decision Support */}
                        <ClinicalPanel metrics={metrics} />

                        {/* Spectral Analysis Dashboard */}
                        <SpectralDashboard analysis={analysis} />

                        {/* Brain Visualization (fMRI Style) */}
                        <div className="bg-medical-panel rounded-xl border border-medical-surface p-4 shadow-medical flex-1 min-h-[300px] flex flex-col relative overflow-hidden">
                            <div className="flex items-center gap-2 mb-4 border-b border-medical-surface pb-2">
                                <Brain className="w-5 h-5 text-medical-primary" />
                                <h3 className="font-bold text-medical-text">CORTICAL ACTIVITY (fMRI)</h3>
                            </div>
                            {/* We use channels buffer for the heatmap. Take the last frame. */}
                            <BrainMRI channelData={channels} analysis={analysis} />

                            <div className="absolute bottom-4 right-4 text-xs font-mono text-medical-muted bg-medical-panel border border-medical-surface px-2 py-1 rounded">
                                Synaptic Gain: {metrics.k}
                            </div>
                        </div>

                        {/* Controls */}
                        <div className="bg-medical-panel rounded-xl border border-medical-surface p-5 shadow-medical">
                            <h3 className="font-bold text-medical-text mb-4 flex items-center gap-2">
                                <Stethoscope className="w-5 h-5 text-medical-accent" />
                                INTERVENTION
                            </h3>
                            <div className="grid grid-cols-2 gap-3 mb-4">
                                <button onClick={() => sendCommand("START")} className="flex items-center justify-center gap-2 p-3 rounded-lg bg-medical-primary text-white hover:bg-blue-700 shadow-sm transition-all font-medium">
                                    <Play className="w-4 h-4" /> Start
                                </button>
                                <button onClick={() => sendCommand("STOP")} className="flex items-center justify-center gap-2 p-3 rounded-lg bg-white border border-medical-surface text-medical-text hover:bg-red-50 hover:text-red-500 hover:border-red-200 shadow-sm transition-all font-medium">
                                    <Square className="w-4 h-4" /> Stop
                                </button>
                            </div>
                            <div className="space-y-2 mb-4">
                                <ScenarioBtn label="NORMAL RHYTHM" color="green" onClick={() => sendCommand("TRIGGER_NORMAL")} />
                                <ScenarioBtn label="INDUCE GENERALIZED SEIZURE" color="red" onClick={() => sendCommand("TRIGGER_SEIZURE")} />
                                <ScenarioBtn label="ANESTHESIA (BURST-SUPP)" color="gray" onClick={() => sendCommand("TRIGGER_SUPPRESSION")} />
                            </div>

                            <h3 className="font-bold text-medical-text mb-2 text-xs uppercase opacity-70">Advanced Triggers</h3>
                            <div className="grid grid-cols-2 gap-2 mb-4">
                                <button onClick={() => sendCommand("TOGGLE_EYES")} className="p-2 border border-medical-surface rounded text-xs font-mono text-medical-text hover:bg-white/5">
                                    👁️ EYES OPEN/CLOSE
                                </button>
                                <button onClick={() => sendCommand("INJECT_SPIKE")} className="p-2 border border-medical-surface rounded text-xs font-mono text-red-400 hover:bg-red-500/10 border-red-900/30">
                                    ⚡ INJECT SPIKE
                                </button>
                            </div>

                            <h3 className="font-bold text-medical-text mb-2 text-xs uppercase opacity-70">Signal Processing</h3>
                            <div className="space-y-2">
                                <button
                                    onClick={toggleICA}
                                    className={`w-full flex items-center justify-between p-2 border rounded text-xs font-bold transition-all ${icaEnabled ? 'bg-indigo-100 text-indigo-700 border-indigo-300' : 'bg-slate-800 text-slate-400 border-slate-700'}`}
                                >
                                    <span>🧹 CLEAN ARTIFACTS (ICA)</span>
                                    <span className="text-[10px]">{icaEnabled ? 'ON' : 'OFF'}</span>
                                </button>
                            </div>

                            <h3 className="font-bold text-medical-text mt-4 mb-2 text-xs uppercase opacity-70">Reporting</h3>
                            <div className="grid grid-cols-2 gap-2">
                                <button onClick={() => sendCommand("GENERATE_REPORT")} className="p-2 border border-medical-surface rounded text-xs font-bold text-medical-primary hover:bg-cyan-500/10">
                                    📄 GEN REPORT
                                </button>
                                <button className="p-2 border border-medical-surface rounded text-xs font-bold text-medical-muted hover:bg-white/5 opacity-50 cursor-not-allowed">
                                    💾 EXPORT EDF+
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: EEG Grid */}
                    <div className="col-span-12 lg:col-span-8 flex flex-col gap-4 h-full">
                        <div className="bg-medical-panel rounded-xl border border-medical-surface shadow-medical flex-1 flex flex-col overflow-hidden relative">
                            <div className="absolute top-2 left-2 z-10 flex items-center gap-4 pointer-events-auto">
                                <div className="flex items-center gap-2 opacity-50">
                                    <Activity className="w-4 h-4 text-medical-primary" />
                                    <span className="text-[10px] font-mono">EEG_MONITOR_20CH</span>
                                </div>

                                {/* MONTAGE SELECTOR */}
                                <select
                                    value={montage}
                                    onChange={(e) => setMontage(e.target.value)}
                                    className="bg-slate-900 border border-slate-700 text-slate-300 text-[10px] rounded px-2 py-1 outline-none focus:border-cyan-500 cursor-pointer"
                                >
                                    <option value="REF">REFERENTIAL (G2=GND)</option>
                                    <option value="BIPOLAR">BIPOLAR (DOUBLE BANANA)</option>
                                </select>
                            </div>
                            <div className="flex-1 relative">
                                <EEGCanvas
                                    dataRef={dataRef}
                                    montage={montage}
                                    playbackData={playbackData}
                                />
                            </div>
                        </div>

                        {/* Metrics Strip */}
                        <div className="h-24 grid grid-cols-2 gap-4">
                            <MetricBox label="PHASE COHERENCE (R)" value={metrics.r} unit="" color="blue" />
                            <MetricBox label="METABOLIC STATE" value={status === 'SUPPRESSED' ? 'LOW' : 'NORMAL'} unit="" color={status === 'SUPPRESSED' ? 'orange' : 'emerald'} />
                        </div>
                    </div>

                </div>
            </div>

            {/* REPORT MODAL */}
            {showReport && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col overflow-hidden">
                        <div className="p-4 border-b flex items-center justify-between bg-slate-50">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2">
                                <Stethoscope className="w-5 h-5 text-medical-primary" />
                                CLINICAL REPORT
                            </h2>
                            <button onClick={() => setShowReport(false)} className="text-slate-400 hover:text-slate-600">
                                ✕
                            </button>
                        </div>
                        <div className="p-6 overflow-y-auto font-mono text-sm leading-relaxed whitespace-pre-wrap text-slate-700">
                            {reportText}
                        </div>
                        <div className="p-4 border-t bg-slate-50 flex justify-end gap-3">
                            <button onClick={() => setShowReport(false)} className="px-4 py-2 text-slate-600 font-bold hover:bg-slate-200 rounded">Close</button>
                            <button onClick={() => window.print()} className="px-4 py-2 bg-medical-primary text-white font-bold rounded hover:bg-cyan-700 shadow-md">
                                Print / Save PDF
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </Layout>
    );
};

const ScenarioBtn = ({ label, color, onClick }) => {
    const colors = {
        green: 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100',
        red: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
        gray: 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
    };
    return (
        <button onClick={onClick} className={`w-full text-left px-4 py-3 rounded-lg border text-xs font-bold transition-all ${colors[color]}`}>
            {label}
        </button>
    )
}

const MetricBox = ({ label, value, unit, color }) => (
    <div className="bg-medical-panel rounded-xl border border-medical-surface shadow-medical p-4 flex items-center justify-between">
        <div>
            <div className="text-xs font-bold text-medical-muted mb-1">{label}</div>
            <div className="text-2xl font-mono font-bold text-medical-text">{value}<span className="text-sm text-medical-muted ml-1">{unit}</span></div>
        </div>
        <div className={`w-2 h-full rounded-full bg-${color}-500 opacity-20`}></div>
    </div>
)

export default Dashboard;
