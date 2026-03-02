import React, { useMemo, useState } from 'react';

const BrainMRI = ({ channelData = [] }) => {
    // -------------------------------------------------------------------------
    // TEXTBOOK MRI VISUALIZATION (High-Fidelity T1 Axial)
    // -------------------------------------------------------------------------
    // Enhanced with Causal Modulation (Synaptic Gain) and 10-20 Anatomical Reference.

    // 1. Synaptic Gain State:
    // Modulates the responsiveness of the cortex. Higher gain = wider/brighter activation.
    const [synapticGain, setSynapticGain] = useState(1.0);
    const [expanded, setExpanded] = useState(false);

    // Sensor Coordinates (Approximate 10-20 System on Axial Slice)
    const sensors = useMemo(() => [
        { id: 'Fp1', x: 35, y: 15 }, { id: 'Fp2', x: 65, y: 15 },
        { id: 'F7', x: 18, y: 30 }, { id: 'F3', x: 32, y: 32 }, { id: 'Fz', x: 50, y: 25 }, { id: 'F4', x: 68, y: 32 }, { id: 'F8', x: 82, y: 30 },
        { id: 'T3', x: 12, y: 50 }, { id: 'C3', x: 28, y: 50 }, { id: 'Cz', x: 50, y: 48 }, { id: 'C4', x: 72, y: 50 }, { id: 'T4', x: 88, y: 50 },
        { id: 'T5', x: 20, y: 72 }, { id: 'P3', x: 35, y: 70 }, { id: 'Pz', x: 50, y: 72 }, { id: 'P4', x: 65, y: 70 }, { id: 'T6', x: 80, y: 72 },
        { id: 'O1', x: 38, y: 88 }, { id: 'O2', x: 62, y: 88 }, { id: 'Oz', x: 50, y: 92 }
    ], []);
    // 2. Activity Threshold State:
    // Filters out background noise/normal rhythm to isolate pathological peaks.
    const [threshold, setThreshold] = useState(0.3);

    // Toggle expansion handler
    const toggleExpand = () => setExpanded(!expanded);

    // Connectivity Lines (Functional Network)
    // We expect 'analysis' prop to contain 'connectivity' list: [{s_idx, t_idx, strength}, ...]
    const renderConnections = () => {
        if (!analysis || !analysis.connectivity) return null;

        return (
            <g className="connections">
                {analysis.connectivity.map((link, i) => {
                    const s = sensors.find(sen => sen.i === link.s_idx);
                    const t = sensors.find(sen => sen.i === link.t_idx);
                    if (!s || !t) return null;

                    // Determine color based on strength or a fixed color
                    const strokeColor = link.strength > 0.7 ? 'rgba(255, 0, 255, 0.8)' : 'rgba(0, 255, 255, 0.8)'; // Magenta for strong, Cyan for weaker
                    const glowColor = link.strength > 0.7 ? 'magenta' : 'cyan';

                    return (
                        <line
                            key={`link-${i}`}
                            x1={s.x} y1={s.y}
                            x2={t.x} y2={t.y}
                            stroke={strokeColor}
                            strokeWidth={link.strength * 2} // Adjust stroke width based on strength
                            strokeLinecap="round"
                            style={{ filter: `drop-shadow(0 0 ${link.strength * 4}px ${glowColor})`, transition: 'stroke-width 0.3s ease-out, filter 0.3s ease-out' }}
                        />
                    );
                })}
            </g>
        );
    };

    return (
        <div
            className={`${expanded
                ? "fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-8 backdrop-blur-xl transition-all duration-300"
                : "relative w-full h-full bg-black flex items-center justify-center overflow-hidden border border-slate-900 bg-slate-950 cursor-pointer hover:border-slate-700 transition-colors"
                }`}
            onClick={!expanded ? toggleExpand : undefined}
        >

            {/* Close Button (Expanded Only) */}
            {expanded && (
                <button
                    onClick={(e) => { e.stopPropagation(); setExpanded(false); }}
                    className="absolute top-6 right-6 text-white/50 hover:text-white bg-white/10 hover:bg-white/20 rounded-full p-2 transition-all z-50"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            )}

            {/* Aspect Ratio Container */}
            <div
                className={`relative aspect-square transition-all duration-500 ease-out flex flex-col items-center justify-center ${expanded ? "h-[85vh]" : "h-full max-h-[600px]"}`}
                onClick={expanded ? (e) => e.stopPropagation() : undefined}
            >
                {/* Title and Controls in Expanded Mode */}
                {expanded && (
                    <div className="absolute -top-20 left-0 right-0 flex justify-between items-end pb-4 border-b border-white/10 w-full mb-4">
                        <div className="text-white font-mono text-xl tracking-[0.2em] opacity-80 flex flex-col gap-1">
                            <div className="flex items-center gap-3">
                                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                CORTICAL PERFUSION MODEL
                            </div>
                            <span className="text-xs text-slate-400 normal-case tracking-normal max-w-xl">
                                Although fMRI measures hemodynamic activity, regions are referenced using the EEG 10–20 system for anatomical correspondence.
                                Synaptic gain modulates cortical responsiveness by amplifying or dampening neural activity.
                            </span>
                        </div>

                        {/* CONTROLS */}
                        <div className="flex flex-col items-end gap-3 bg-black/40 p-3 rounded border border-white/10">
                            {/* Synaptic Gain */}
                            <div className="flex flex-col items-end gap-1">
                                <label className="text-[10px] text-cyan-400 font-mono tracking-wider">SYNAPTIC GAIN: {synapticGain.toFixed(1)}x</label>
                                <input
                                    type="range" min="0.5" max="3.0" step="0.1"
                                    value={synapticGain} onChange={(e) => setSynapticGain(parseFloat(e.target.value))}
                                    className="w-48 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                />
                            </div>
                            {/* Activity Threshold */}
                            <div className="flex flex-col items-end gap-1">
                                <label className="text-[10px] text-red-400 font-mono tracking-wider">NOISE THRESHOLD: {threshold.toFixed(2)}</label>
                                <input
                                    type="range" min="0.0" max="1.0" step="0.05"
                                    value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))}
                                    className="w-48 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* VISUALIZATION CORE */}
                <div className="relative w-full h-full">
                    {/* LAYER 1: The Textbook T1 MRI (Structural Anatomy) */}
                    <img
                        src="/mri_textbook.png"
                        alt="Axial T1 MRI"
                        className="absolute inset-0 w-full h-full object-contain"
                        style={{ filter: 'contrast(1.1) brightness(0.9)' }}
                    />

                    {/* LAYER 2: Metabolic Perfusion Map (Intrinsic Staining) */}
                    <svg viewBox="0 0 100 100" className="absolute inset-0 w-full h-full z-10" style={{ mixBlendMode: 'overlay' }}>
                        <defs>
                            <mask id="tissue-mask">
                                <image href="/mri_mask.png" x="0" y="0" width="100" height="100" />
                            </mask>
                            <filter id="perfusion-blur" x="-50%" y="-50%" width="200%" height="200%">
                                <feGaussianBlur stdDeviation={6 * synapticGain} result="blur" /> {/* Blur/Spread increases with Gain */}
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>

                            {sensors.map((s, i) => {
                                let val = (channelData[i] || 0) / 40.0;
                                val = val * synapticGain; // Causal Modulation
                                val = Math.min(2.5, Math.max(0, val));

                                // THRESHOLD FILTERING
                                // If value is below threshold, render it transparent to "clean" the map
                                if (val < threshold) val = 0;

                                let stops = [];
                                if (val === 0) {
                                    stops = [<stop key="0" offset="0%" stopColor="#000000" stopOpacity="0" />, <stop key="1" offset="100%" stopColor="#000000" stopOpacity="0" />];
                                } else if (val < 0.2) {
                                    stops = [<stop key="0" offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />, <stop key="1" offset="100%" stopColor="#1d4ed8" stopOpacity="0" />];
                                } else if (val < 0.8) {
                                    stops = [<stop key="0" offset="0%" stopColor="#22c55e" stopOpacity="0.6" />, <stop key="1" offset="100%" stopColor="#22c55e" stopOpacity="0" />];
                                } else if (val < 1.5) {
                                    stops = [<stop key="0" offset="0%" stopColor="#eab308" stopOpacity="0.9" />, <stop key="1" offset="100%" stopColor="#a16207" stopOpacity="0" />];
                                } else {
                                    stops = [<stop key="0" offset="0%" stopColor="#ef4444" stopOpacity="1" />, <stop key="1" offset="100%" stopColor="#7f1d1d" stopOpacity="0" />];
                                }

                                return (
                                    <radialGradient key={`grad-${s.id}`} id={`grad-${s.id}`}>
                                        {stops}
                                    </radialGradient>
                                );
                            })}
                        </defs>

                        <g mask="url(#tissue-mask)" filter="url(#perfusion-blur)">
                            {sensors.map((s, i) => {
                                // Double check threshold for fill rendering optimization
                                let rawVal = (channelData[i] || 0) / 40.0 * synapticGain;
                                if (rawVal < threshold) return null;

                                return (
                                    <circle
                                        key={s.id} cx={s.x} cy={s.y}
                                        r={15 * (1 + (synapticGain - 1) * 0.5)} // Radius expands with Gain
                                        fill={`url(#grad-${s.id})`}
                                        style={{ opacity: 1 }}
                                    />
                                )
                            })}
                        </g>

                        {/* LAYER 3: 10-20 Electrodes Overlay (Labels) */}
                        <g style={{ pointerEvents: 'none' }}>
                            {sensors.map((s) => (
                                <g key={`label-group-${s.id}`}>
                                    <text
                                        x={s.x} y={s.y} dy="0.35em"
                                        textAnchor="middle"
                                        stroke="#000000"
                                        strokeWidth="0.8"
                                        fill="#ffffff"
                                        fontSize="2.8"
                                        fontFamily="monospace"
                                        fontWeight="900"
                                        paintOrder="stroke"
                                        style={{ filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,1))' }}
                                    >
                                        {s.id}
                                    </text>
                                </g>
                            ))}
                        </g>
                    </svg>

                    {/* ORIENTATION MARKERS (L/R) - Expanded Only */}
                    {expanded && (
                        <div className="absolute inset-x-2 top-1/2 -translate-y-1/2 flex justify-between pointer-events-none">
                            <div className="text-white/80 font-bold text-xl font-mono bg-black/50 px-2 rounded border border-white/20">L</div>
                            <div className="text-white/80 font-bold text-xl font-mono bg-black/50 px-2 rounded border border-white/20">R</div>
                        </div>
                    )}
                </div>

                {/* DETAILED LEGEND - Expanded Only */}
                {expanded && (
                    <div className="absolute bottom-4 right-4 flex flex-col gap-2 pointer-events-none">
                        <div className="bg-black/80 p-3 rounded border border-white/10 backdrop-blur text-[10px] w-48">
                            <div className="font-bold text-slate-400 mb-2 border-b border-white/10 pb-1">CLINICAL PERFUSION SCALE</div>

                            {/* Scale Items */}
                            <div className="grid grid-cols-[12px_1fr] gap-2 items-center mb-1">
                                <div className="w-3 h-3 rounded-full bg-blue-600"></div>
                                <span className="text-slate-400">HYPOMETABOLIC (Suppression)</span>
                            </div>
                            <div className="grid grid-cols-[12px_1fr] gap-2 items-center mb-1">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span className="text-slate-400">NORMAL (Physiologic)</span>
                            </div>
                            <div className="grid grid-cols-[12px_1fr] gap-2 items-center mb-1">
                                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                <span className="text-slate-400">HYPERMETABOLIC (Pre-Ictal)</span>
                            </div>
                            <div className="grid grid-cols-[12px_1fr] gap-2 items-center">
                                <div className="w-3 h-3 rounded-full bg-red-600 animate-pulse"></div>
                                <span className="font-bold text-red-400">ICTAL / LESIONAL</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Footer Note (Collapsed Mode Only) */}
                {!expanded && (
                    <div className="absolute bottom-2 left-0 right-0 text-[10px] text-center text-cyan-400 font-mono px-4 opacity-90 animate-pulse cursor-pointer">
                        CLICK TO EXPAND FOR CLINICAL ANALYSIS
                    </div>
                )}

            </div>
        </div>
    );
};

export default BrainMRI;
