import React, { useMemo } from 'react';
import { motion } from 'framer-motion';

const BrainNetwork = ({ activeNodes = [], globalActivity = 0 }) => {
    // Define node positions approximating a top-down brain view (Anterior at top, Posterior at bottom)
    // Normalized 0-100 coordinates
    const nodes = [
        // Frontal
        { id: 'FP1', x: 35, y: 15, label: 'FP1' }, { id: 'FP2', x: 65, y: 15, label: 'FP2' },
        { id: 'F7', x: 20, y: 30, label: 'F7' }, { id: 'F3', x: 40, y: 30, label: 'F3' }, { id: 'Fz', x: 50, y: 30, label: 'Fz' }, { id: 'F4', x: 60, y: 30, label: 'F4' }, { id: 'F8', x: 80, y: 30, label: 'F8' },

        // Central
        { id: 'T3', x: 15, y: 50, label: 'T3' }, { id: 'C3', x: 35, y: 50, label: 'C3' }, { id: 'Cz', x: 50, y: 50, label: 'Cz' }, { id: 'C4', x: 65, y: 50, label: 'C4' }, { id: 'T4', x: 85, y: 50, label: 'T4' },

        // Parietal
        { id: 'T5', x: 20, y: 70, label: 'T5' }, { id: 'P3', x: 40, y: 70, label: 'P3' }, { id: 'Pz', x: 50, y: 70, label: 'Pz' }, { id: 'P4', x: 60, y: 70, label: 'P4' }, { id: 'T6', x: 80, y: 70, label: 'T6' },

        // Occipital
        { id: 'O1', x: 35, y: 85, label: 'O1' }, { id: 'O2', x: 65, y: 85, label: 'O2' }
    ];

    // Generate edges (simple nearest neighbor logic for visualization)
    const edges = useMemo(() => {
        const links = [];
        nodes.forEach((source, i) => {
            nodes.forEach((target, j) => {
                if (i < j) {
                    const dist = Math.sqrt(Math.pow(source.x - target.x, 2) + Math.pow(source.y - target.y, 2));
                    if (dist < 25) { // Threshold for connection
                        links.push({ source, target, key: `${source.id}-${target.id}` });
                    }
                }
            });
        });
        return links;
    }, []);

    return (
        <div className="relative w-full h-full flex items-center justify-center p-4">
            {/* Brain Outline Background (Simplified Ellipse) */}
            <svg viewBox="0 0 100 100" className="w-full h-full max-w-[400px] opacity-10 pointer-events-none absolute">
                <ellipse cx="50" cy="50" rx="40" ry="45" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="1" />
            </svg>

            <svg viewBox="0 0 100 100" className="w-full h-full max-w-[400px] overflow-visible">
                <defs>
                    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="2" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {/* Edges */}
                {edges.map(edge => (
                    <line
                        key={edge.key}
                        x1={edge.source.x}
                        y1={edge.source.y}
                        x2={edge.target.x}
                        y2={edge.target.y}
                        stroke="#cbd5e1" // Slate 300
                        strokeWidth="0.5"
                        className="transition-all duration-300"
                    />
                ))}

                {/* Dynamic Edges (Active) */}
                {edges.map((edge, i) => (
                    Math.random() > 0.8 && ( // Random active edges for demo effect, real app would bind to coherence matrix
                        <line
                            key={`active-${edge.key}`}
                            x1={edge.source.x}
                            y1={edge.source.y}
                            x2={edge.target.x}
                            y2={edge.target.y}
                            stroke="#3b82f6"
                            strokeWidth="1"
                            strokeOpacity={globalActivity} // Pulse with activity
                            className="transition-opacity duration-100"
                        />
                    )
                ))}

                {/* Nodes */}
                {nodes.map((node, i) => (
                    <g key={node.id}>
                        {/* Halo Effect */}
                        <circle
                            cx={node.x}
                            cy={node.y}
                            r={3 + Math.random() * globalActivity * 3}
                            fill="#3b82f6"
                            opacity={0.1 + globalActivity * 0.3}
                            className="transition-all duration-75"
                        />

                        {/* Core Node */}
                        <circle
                            cx={node.x}
                            cy={node.y}
                            r="2.5"
                            fill="white"
                            stroke="#0f172a"
                            strokeWidth="1.5"
                            className="transition-all duration-300 hover:scale-150 cursor-pointer"
                        />
                        {/* Label */}
                        <text x={node.x} y={node.y + 6} textAnchor="middle" fontSize="3" fill="#64748b" className="font-mono font-bold">{node.label}</text>
                    </g>
                ))}

                <text x="50" y="5" textAnchor="middle" fontSize="4" fill="#cbd5e1" letterSpacing="0.2em" className="font-bold">ANTERIOR</text>
                <text x="50" y="98" textAnchor="middle" fontSize="4" fill="#cbd5e1" letterSpacing="0.2em" className="font-bold">POSTERIOR</text>
            </svg>
        </div>
    );
};

export default BrainNetwork;
