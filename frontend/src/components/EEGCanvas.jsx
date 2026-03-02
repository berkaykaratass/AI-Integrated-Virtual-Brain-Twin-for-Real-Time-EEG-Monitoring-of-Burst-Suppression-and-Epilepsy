import React, { useRef, useEffect } from 'react';

const EEGCanvas = ({ dataRef, analysisRef, montage = 'REF', playbackData = null }) => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);

    // --- MONTAGE DEFINITIONS ---
    const MONTAGES = {
        'REF': {
            left: { indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], labels: ["Fp1", "F7", "F3", "T3", "C3", "T5", "P3", "O1", "Fz", "Pz"] },
            right: { indices: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19], labels: ["Fp2", "F8", "F4", "T4", "C4", "T6", "P4", "O2", "Cz", "Oz"] }
        },
        'BIPOLAR': { // "Double Banana" (Longitudinal Bipolar)
            // Pairs are indices of channels: ChA - ChB
            // Left Chain
            left: {
                pairs: [[0, 1], [1, 3], [3, 5], [5, 7], [0, 2], [2, 4], [4, 6], [6, 7]],
                labels: ["Fp1-F7", "F7-T3", "T3-T5", "T5-O1", "Fp1-F3", "F3-C3", "C3-P3", "P3-O1"]
            },
            right: {
                pairs: [[10, 11], [11, 13], [13, 15], [15, 17], [10, 12], [12, 14], [14, 16], [16, 17]],
                labels: ["Fp2-F8", "F8-T4", "T4-T6", "T6-O2", "Fp2-F4", "F4-C4", "C4-P4", "P4-O2"]
            }
        }
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // Resize Handler
        const resizeCanvas = () => {
            canvas.width = containerRef.current.clientWidth;
            canvas.height = containerRef.current.clientHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        const ctx = canvas.getContext('2d');
        let animationFrameId;

        // Config
        const PIXELS_PER_SECOND = 150;
        const SAMPLE_RATE = 200;
        const speed = PIXELS_PER_SECOND / SAMPLE_RATE; // px per sample

        // Buffer for LIVE mode (20 channels)
        // Store simple array of values per channel
        // e.g. liveBuffer[0] = [v1, v2, ...]
        let liveBuffer = Array(20).fill().map(() => []);
        const maxDataPoints = Math.ceil(4000); // 20s buffer approx

        const render = () => {
            // 1. DATA INGESTION (Only if live)
            if (!playbackData && dataRef.current) {
                while (dataRef.current.queue.length > 0) {
                    const packet = dataRef.current.queue.shift(); // [v0...v19]
                    if (packet) {
                        for (let ch = 0; ch < 20; ch++) {
                            liveBuffer[ch].push(packet[ch]);
                            if (liveBuffer[ch].length > maxDataPoints) liveBuffer[ch].shift();
                        }
                    }
                }
            }

            // 2. DETERMINE ACTIVE SOURCE
            // If playbackData exists, use it. Otherwise use liveBuffer.
            // playbackData structure is also Array(20) of arrays of values
            const activeBuffer = playbackData || liveBuffer;
            if (!activeBuffer || activeBuffer.length === 0) {
                animationFrameId = requestAnimationFrame(render);
                return;
            }

            const width = canvas.width;
            const height = canvas.height;

            // Background
            ctx.fillStyle = '#0f172a'; // Slate 900
            ctx.fillRect(0, 0, width, height);

            // Grid (Time)
            ctx.lineWidth = 0.5;
            ctx.strokeStyle = '#334155'; // Slate 700
            ctx.beginPath();
            // In playback, grid is static relative to data start? Or scrolling?
            // Simplified: Draw static grid lines every 1 sec (150px)
            for (let x = width; x > 0; x -= PIXELS_PER_SECOND) {
                ctx.moveTo(x, 0); ctx.lineTo(x, height);
            }
            ctx.stroke();

            // RENDER TRACES
            const currentLayout = MONTAGES[montage] || MONTAGES['REF'];
            const montageGap = 30;
            const blockHeight = (height - montageGap) / 2;
            const gain = 0.5;

            const drawGroup = (groupData, startY, count) => {
                const chHeight = blockHeight / count;
                const bufferLen = activeBuffer[0] ? activeBuffer[0].length : 0;

                // We draw the last 'width/speed' samples that fit on screen
                const capacity = Math.ceil(width / speed);
                const startIndex = Math.max(0, bufferLen - capacity);

                groupData.labels.forEach((label, i) => {
                    const base_y = startY + (i + 0.5) * chHeight;

                    // Label
                    ctx.fillStyle = '#1e293b';
                    ctx.fillRect(0, base_y - 8, 55, 16);
                    ctx.fillStyle = '#cbd5e1';
                    ctx.font = 'bold 10px monospace';
                    ctx.textAlign = 'left';
                    ctx.fillText(label, 4, base_y + 3);

                    // Trace
                    ctx.strokeStyle = '#22d3ee';
                    ctx.lineWidth = 1.0;
                    ctx.beginPath();

                    let hasSignal = false;
                    for (let j = startIndex; j < bufferLen; j++) {
                        const x = width - (bufferLen - 1 - j) * speed;
                        let val = 0;

                        // Calculate Value
                        if (montage === 'BIPOLAR' && groupData.pairs) {
                            const pair = groupData.pairs[i];
                            // Ensure data exists
                            if (activeBuffer[pair[0]] && activeBuffer[pair[1]]) {
                                val = activeBuffer[pair[0]][j] - activeBuffer[pair[1]][j];
                            }
                        } else if (groupData.indices) {
                            const idx = groupData.indices[i];
                            if (activeBuffer[idx]) {
                                val = activeBuffer[idx][j];
                            }
                        }

                        // Soft Clamp for viz
                        if (val > 500) val = 500; if (val < -500) val = -500;
                        const y = base_y - (val * gain);

                        if (!hasSignal) { ctx.moveTo(x, y); hasSignal = true; }
                        else ctx.lineTo(x, y);
                    }
                    ctx.stroke();
                });
            };

            const leftCount = currentLayout.left.labels.length;
            const rightCount = currentLayout.right.labels.length;

            if (activeBuffer && activeBuffer[0] && activeBuffer[0].length > 0) {
                drawGroup(currentLayout.left, 0, leftCount);

                // Divider
                ctx.fillStyle = '#475569';
                ctx.textAlign = 'center';
                ctx.font = '10px monospace';
                ctx.fillText("LEFT HEMISPHERE", width / 2, blockHeight + 12);
                ctx.fillText("RIGHT HEMISPHERE", width / 2, height - 2);

                drawGroup(currentLayout.right, blockHeight + montageGap, rightCount);
            }

            animationFrameId = requestAnimationFrame(render);
        };
        render();

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            cancelAnimationFrame(animationFrameId);
        };
    }, [montage, playbackData]);

    return (
        <div ref={containerRef} className="w-full h-full relative bg-slate-950 border border-slate-800 rounded-sm overflow-hidden">
            <canvas ref={canvasRef} className="block" />
        </div>
    );
};

export default EEGCanvas;
