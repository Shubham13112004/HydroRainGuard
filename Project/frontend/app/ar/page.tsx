'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Info } from 'lucide-react';
import type { AssessmentResponse } from '@/lib/types';

export default function ARPage() {
  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    const stored = localStorage.getItem('hydro_result');
    if (stored) setData(JSON.parse(stored));
  }, []);

  const structures3D = [
    {
      name: 'Rooftop Storage Tank',
      color: '#0d5c8c',
      shape: 'cylinder',
      desc: 'Underground/ground-level storage tank. Captures rooftop runoff via first-flush diverter.',
      emoji: '🏗️',
    },
    {
      name: 'Recharge Pit',
      color: '#27ae60',
      shape: 'box',
      desc: 'Gravel-filled pit (1.5m × 1.5m × 2m). Allows water to percolate into the water table.',
      emoji: '🕳️',
    },
    {
      name: 'Recharge Well',
      color: '#e67e22',
      shape: 'cylinder-deep',
      desc: 'Deep borewell (200–300mm dia, 10–30m). Channels water directly into deep aquifers.',
      emoji: '🛢️',
    },
    {
      name: 'Percolation Tank',
      color: '#8e44ad',
      shape: 'pond',
      desc: 'Open surface tank with large area. Slow percolation over a large footprint.',
      emoji: '🏞️',
    },
  ];

  const topStructure = data?.recommended_structures?.[selected];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-800">
        <Link href="/results" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Results
        </Link>
        <span className="text-gray-600">|</span>
        <h1 className="font-bold text-lg">💧 AR Visualization — HYDRO RAIN GUARD</h1>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 3D Viewer */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-2xl overflow-hidden" style={{ height: '500px' }}>
            <div
              dangerouslySetInnerHTML={{
                __html: `
                <style>
                  a-scene { width: 100%; height: 500px; display: block; }
                </style>
                <a-scene embedded background="color: #1a1a2e" fog="type: linear; color: #1a1a2e; near: 10; far: 50">
                  <!-- Lighting -->
                  <a-light type="ambient" color="#ffffff" intensity="0.4"></a-light>
                  <a-light type="directional" position="5 10 5" color="#ffffff" intensity="1"></a-light>
                  <a-light type="point" position="0 5 0" color="#0d5c8c" intensity="0.5"></a-light>

                  <!-- Ground grid -->
                  <a-grid position="0 0 0" color="#333" opacity="0.3"></a-grid>
                  <a-plane position="0 0 -2" rotation="-90 0 0" width="20" height="20" color="#1a2a1a" opacity="0.8" shadow></a-plane>

                  <!-- Building representation -->
                  <a-box position="0 1 0" width="4" height="2" depth="3" color="#d0cfc9" opacity="0.9" shadow>
                    <!-- Roof -->
                    <a-box position="0 1.2 0" width="4.2" height="0.2" depth="3.2" color="#8B4513"></a-box>
                  </a-box>

                  <!-- Rooftop tank (always shown) -->
                  <a-cylinder position="1.5 3.2 0" radius="0.4" height="0.8" color="#0d5c8c" opacity="0.9" shadow>
                    <a-animation attribute="rotation" to="0 360 0" dur="8000" repeat="indefinite" easing="linear"></a-animation>
                  </a-cylinder>
                  <a-text value="Storage\nTank" position="1.5 4.2 0" color="#00bcd4" scale="0.8 0.8 0.8" align="center"></a-text>

                  <!-- Downpipe -->
                  <a-cylinder position="-2 1 0" radius="0.06" height="2" color="#444" rotation="0 0 0"></a-cylinder>

                  <!-- Recharge pit (underground, shown as glowing box) -->
                  <a-box position="-3.5 -0.5 0" width="1.5" height="1.5" depth="1.5" color="#27ae60" opacity="0.7" shadow>
                    <a-animation attribute="scale" from="1 1 1" to="1.05 1.05 1.05" dur="2000" repeat="indefinite" direction="alternate" easing="ease-in-out"></a-animation>
                  </a-box>
                  <a-text value="Recharge\nPit" position="-3.5 0.8 0" color="#27ae60" scale="0.8 0.8 0.8" align="center"></a-text>

                  <!-- Flow pipe connecting building to pit -->
                  <a-cylinder position="-2.7 0.1 0" radius="0.05" height="1.6" color="#00bcd4" rotation="0 0 90" opacity="0.8"></a-cylinder>

                  <!-- Recharge well -->
                  <a-cylinder position="3.5 0 0" radius="0.25" height="3" color="#e67e22" opacity="0.85" shadow></a-cylinder>
                  <a-cylinder position="3.5 -1.5 0" radius="0.2" height="5" color="#c0392b" opacity="0.5"></a-cylinder>
                  <a-text value="Recharge\nWell" position="3.5 2 0" color="#e67e22" scale="0.8 0.8 0.8" align="center"></a-text>

                  <!-- Water flow particles effect -->
                  <a-sphere position="-2 0.8 0" radius="0.08" color="#00bcd4" opacity="0.8">
                    <a-animation attribute="position" from="-2 0.8 0" to="-3 0.1 0" dur="2000" repeat="indefinite" easing="ease-in"></a-animation>
                    <a-animation attribute="opacity" from="1" to="0" dur="2000" repeat="indefinite"></a-animation>
                  </a-sphere>

                  <!-- Water level indicator in pit -->
                  <a-box position="-3.5 -0.8 0" width="1.3" height="0.4" depth="1.3" color="#00bcd4" opacity="0.5">
                    <a-animation attribute="position" from="-3.5 -1.1 0" to="-3.5 -0.5 0" dur="3000" repeat="indefinite" direction="alternate" easing="ease-in-out"></a-animation>
                  </a-box>

                  <!-- Labels floating -->
                  <a-text value="HYDRO RAIN GUARD" position="0 5.5 -2" color="#ffffff" scale="1.2 1.2 1.2" align="center"></a-text>
                  <a-text value="Rainwater Harvesting System" position="0 4.9 -2" color="#00bcd4" scale="0.7 0.7 0.7" align="center"></a-text>

                  <!-- Camera -->
                  <a-camera position="0 3 9" look-controls="enabled: true" wasd-controls="enabled: false">
                    <a-cursor color="#ffffff" opacity="0.5"></a-cursor>
                  </a-camera>
                </a-scene>
              `
              }}
            />
          </div>
          <p className="text-gray-400 text-xs mt-2 text-center">Interactive 3D view — click and drag to rotate • Scroll to zoom</p>
        </div>

        {/* Info Panel */}
        <div className="space-y-4">
          <div className="bg-gray-800 rounded-2xl p-5">
            <h2 className="font-bold text-white mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" /> System Components
            </h2>
            <div className="space-y-2">
              {[
                { color: '#0d5c8c', name: 'Rooftop Storage Tank', desc: 'Blue cylinder on roof' },
                { color: '#27ae60', name: 'Recharge Pit', desc: 'Green underground box' },
                { color: '#e67e22', name: 'Recharge Well', desc: 'Orange deep cylinder' },
                { color: '#00bcd4', name: 'Water Flow', desc: 'Animated blue particles' },
              ].map((c, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-gray-700 rounded-xl">
                  <div className="w-4 h-4 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                  <div>
                    <p className="text-sm font-semibold">{c.name}</p>
                    <p className="text-xs text-gray-400">{c.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {data && (
            <div className="bg-gray-800 rounded-2xl p-5">
              <h2 className="font-bold text-white mb-3">📊 Your Assessment</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Roof Area</span>
                  <span className="font-bold">{data.request.roof_area} m²</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Annual Runoff</span>
                  <span className="font-bold text-cyan-400">{(data.runoff.annual_runoff_volume/1000).toFixed(1)} KL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Top Structure</span>
                  <span className="font-bold text-green-400 text-xs">{data.recommended_structures[0]?.structure_type}</span>
                </div>
              </div>
            </div>
          )}

          <div className="bg-blue-900/40 border border-blue-800 rounded-2xl p-4">
            <p className="text-xs text-blue-300 leading-relaxed">
              📱 <strong>On mobile:</strong> Open this page in Chrome on Android for WebXR AR mode. Point your camera at a flat surface to place the 3D model in your environment.
            </p>
          </div>

          <Link href="/results" className="block w-full text-center bg-primary-700 hover:bg-primary-800 text-white font-bold py-3 rounded-xl transition-colors">
            ← Back to Results
          </Link>
        </div>
      </div>
    </div>
  );
}
