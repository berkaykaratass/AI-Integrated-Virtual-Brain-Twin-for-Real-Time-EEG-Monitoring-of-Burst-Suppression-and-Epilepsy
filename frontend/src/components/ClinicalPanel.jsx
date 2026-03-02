import React from 'react';
import { AlertTriangle, ShieldCheck, ZapOff, Activity } from 'lucide-react';

const ClinicalPanel = ({ metrics }) => {
    const bsr = (metrics.bsr * 100).toFixed(1); // Percentage
    const reserve = (metrics.metabolic_reserve * 100).toFixed(1);
    const decision = metrics.clinical_decision || "INITIALIZING";
    const alertLevel = metrics.alert_level || "GREEN";

    const getAlertStyle = () => {
        if (alertLevel === 'RED') return 'bg-red-50 text-red-700 border-red-200 animate-pulse';
        if (alertLevel === 'YELLOW') return 'bg-yellow-50 text-yellow-700 border-yellow-200';
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    };

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col gap-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                <ShieldCheck className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-800 text-sm">CLINICAL DECISION SUPPORT</h3>
            </div>

            {/* Decision Banner */}
            <div className={`p-4 rounded-lg border flex items-center gap-3 ${getAlertStyle()}`}>
                <AlertTriangle className="w-6 h-6 flex-shrink-0" />
                <div>
                    <div className="text-xs font-bold opacity-70">MECHANISTIC ANALYSIS</div>
                    <div className="text-lg font-bold leading-tight">{decision}</div>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-4">

                {/* BSR Gauge */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-slate-500">BURST SUPPRESSION (BSR)</span>
                        <span className="text-xs font-mono text-slate-400">Target: 50-80%</span>
                    </div>
                    <div className="text-2xl font-mono font-bold text-slate-700 mb-1">{bsr}%</div>
                    {/* Progress Bar */}
                    <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-300 ${metrics.bsr > 0.8 ? 'bg-red-500' : (metrics.bsr < 0.1 ? 'bg-slate-400' : 'bg-green-500')}`}
                            style={{ width: `${Math.min(100, bsr)}%` }}
                        />
                    </div>
                </div>

                {/* Metabolic Reserve */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-slate-500">METABOLIC RESERVE</span>
                        <span className="text-xs font-mono text-slate-400">Model: Synaptic</span>
                    </div>
                    <div className="text-2xl font-mono font-bold text-slate-700 mb-1">{reserve}%</div>
                    {/* Progress Bar */}
                    <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-300 ${metrics.metabolic_reserve < 0.3 ? 'bg-red-500' : 'bg-blue-500'}`}
                            style={{ width: `${Math.min(100, reserve)}%` }}
                        />
                    </div>
                </div>
            </div>

            <div className="text-[10px] text-slate-400 text-center">
                * Model calibration based on standard physiological synaptic recovery rates.
            </div>
        </div>
    );
};

export default ClinicalPanel;
