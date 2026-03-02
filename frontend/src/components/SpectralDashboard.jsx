import React, { useMemo } from 'react';
import { Activity, BarChart2 } from 'lucide-react';

const SpectralDashboard = ({ analysis }) => {
    // Process spectral data to get mean power per band
    const bands = useMemo(() => {
        if (!analysis || !analysis.spectral) return [];

        const spectral = analysis.spectral;
        const processed = [
            { name: 'DELTA', range: '0.5-4 Hz', color: 'bg-indigo-500', raw: spectral.Delta || [] },
            { name: 'THETA', range: '4-8 Hz', color: 'bg-teal-500', raw: spectral.Theta || [] },
            { name: 'ALPHA', range: '8-13 Hz', color: 'bg-emerald-500', raw: spectral.Alpha || [] },
            { name: 'BETA', range: '13-30 Hz', color: 'bg-amber-500', raw: spectral.Beta || [] },
            { name: 'GAMMA', range: '>30 Hz', color: 'bg-rose-500', raw: spectral.Gamma || [] },
        ];

        // Calculate Mean Power for each band
        const totalPower = processed.reduce((acc, band) => {
            const bandMean = band.raw.reduce((a, b) => a + b, 0) / (band.raw.length || 1);
            band.mean = bandMean;
            return acc + bandMean;
        }, 0);

        // Calculate Relative Power (%)
        return processed.map(band => ({
            ...band,
            percent: totalPower > 0 ? (band.mean / totalPower) * 100 : 0
        }));
    }, [analysis]);

    if (!analysis) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col gap-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2 mb-1">
                <BarChart2 className="w-4 h-4 text-slate-500" />
                <h3 className="font-bold text-slate-700 text-xs tracking-wider">SPECTRAL POWER DENSITY</h3>
            </div>

            <div className="space-y-3">
                {bands.map((band) => (
                    <div key={band.name} className="group">
                        <div className="flex justify-between items-end mb-1">
                            <div className="flex items-baseline gap-2">
                                <span className="font-bold text-xs text-slate-600 w-12">{band.name}</span>
                                <span className="text-[10px] text-slate-400 font-mono hidden group-hover:inline">{band.range}</span>
                            </div>
                            <span className="font-mono text-xs font-bold text-slate-700">{band.percent.toFixed(1)}%</span>
                        </div>

                        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className={`h-full ${band.color} transition-all duration-300 ease-out`}
                                style={{ width: `${band.percent}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* Dominant Rhythm Indicator */}
            <div className="mt-2 pt-2 border-t border-slate-100 text-center">
                <span className="text-[10px] text-slate-400 uppercase tracking-wide">Dominant Rhythm: </span>
                <span className="text-xs font-bold text-slate-700">
                    {bands.reduce((prev, current) => (prev.percent > current.percent) ? prev : current, bands[0]).name}
                </span>
            </div>
        </div>
    );
};

export default SpectralDashboard;
