'use client';

import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { ArrowLeft, Info, Layers, Tag, Smartphone } from 'lucide-react';

import type { AssessmentResponse } from '@/lib/types';
import { formatLiters } from '@/lib/utils';
import { useI18n } from '@/lib/i18n';

/* three.js touches `window` at module scope — browser only. */
const ARViewer = dynamic(() => import('@/components/ARViewer'), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

const ARButton = dynamic(
  () => import('@react-three/xr').then((m) => m.ARButton),
  { ssr: false },
);

const LEGEND_STRUCTURE_KEYS: Record<string, string> = {
  'Rooftop Storage Tank': 'ar.legend.tank',
  'Recharge Pit': 'ar.legend.pit',
  'Recharge Well / Borewell Recharge': 'ar.legend.well',
  'Percolation Tank': 'ar.legend.tankPercolation',
  'Soak Pit / French Drain': 'ar.legend.soakPit',
};

export default function ARPage() {
  const { t, structureLabel } = useI18n();

  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [selected, setSelected] = useState(0);
  const [cutaway, setCutaway] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [inAR, setInAR] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('hydro_result');
    if (stored) {
      try {
        setData(JSON.parse(stored));
      } catch {
        setData(null);
      }
    }
    setLoading(false);
  }, []);

  const structures = data?.recommended_structures ?? [];
  const structure = structures[selected] ?? structures[0] ?? null;

  const labels = useMemo(
    () => ({
      building: t('ar.building'),
      tank: t('ar.legend.tank'),
      pipe: t('ar.legend.pipe'),
      structure: structure ? structureLabel(structure.structure_type) : '',
    }),
    [t, structure, structureLabel],
  );

  /* ---------- no assessment yet ---------- */
  if (!loading && !data) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-5">🏗️</div>
          <h1 className="text-2xl font-bold mb-3">{t('ar.title')}</h1>
          <p className="text-gray-400 mb-7">{t('ar.noData')}</p>
          <Link
            href="/assess"
            className="inline-block bg-primary-700 hover:bg-primary-800 text-white font-bold px-7 py-3 rounded-xl transition-colors"
          >
            {t('ar.noDataCta')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* ---- header ---- */}
      <div className="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Link
            href="/results"
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">{t('ar.back')}</span>
          </Link>
          <span className="text-gray-600">|</span>
          <h1 className="font-bold text-sm sm:text-lg truncate">
            💧 {t('ar.title')}
          </h1>
        </div>

        {/* AR entry — only meaningful on a WebXR AR device */}
        <div className="shrink-0 [&>button]:!bg-primary-700 [&>button]:!text-white [&>button]:!rounded-lg [&>button]:!px-4 [&>button]:!py-2 [&>button]:!text-sm [&>button]:!font-semibold [&>button]:!border-0 [&>button]:!cursor-pointer">
          <ARButton
            sessionInit={{
              optionalFeatures: ['hit-test', 'dom-overlay'],
            }}
          />
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ---- 3D viewport ---- */}
        <div className="lg:col-span-2 space-y-3">
          <div
            className="bg-gray-800 rounded-2xl overflow-hidden relative"
            style={{ height: 'min(62vh, 520px)' }}
          >
            <ARViewer
              structure={structure}
              roofArea={data?.request?.roof_area ?? 100}
              cutaway={cutaway}
              showLabels={showLabels && !inAR}
              labels={labels}
            />
          </div>

          {/* ---- view controls ---- */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setCutaway((v) => !v)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-colors ${
                cutaway
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
              }`}
            >
              <Layers className="w-4 h-4" />
              {t('ar.view.cutaway')}
            </button>

            <button
              type="button"
              onClick={() => setShowLabels((v) => !v)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-colors ${
                showLabels
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
              }`}
            >
              <Tag className="w-4 h-4" />
              {t('ar.showLabels')}
            </button>

            <span className="ml-auto text-xs text-gray-500">
              {t('ar.desktopNote')}
            </span>
          </div>

          <div className="bg-blue-900/30 border border-blue-800/60 rounded-xl p-3.5 flex gap-2.5">
            <Smartphone className="w-4 h-4 text-blue-300 shrink-0 mt-0.5" />
            <p className="text-xs text-blue-200 leading-relaxed">
              {t('ar.mobileNote')}
            </p>
          </div>
        </div>

        {/* ---- side panel ---- */}
        <div className="space-y-4">
          {/* structure picker */}
          <div className="bg-gray-800 rounded-2xl p-5">
            <h2 className="font-bold text-white mb-3 text-sm">
              {t('ar.selectStructure')}
            </h2>
            <div className="space-y-2">
              {structures.map((s, i) => (
                <button
                  key={`${s.structure_type}-${i}`}
                  type="button"
                  onClick={() => setSelected(i)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl border transition-colors ${
                    i === selected
                      ? 'bg-primary-700/30 border-primary-600 text-white'
                      : 'bg-gray-700/50 border-transparent text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold truncate">
                      {structureLabel(s.structure_type)}
                    </span>
                    <span className="text-xs text-cyan-300 shrink-0">
                      {s.suitability_score}/100
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* dimensions */}
          {structure && (
            <div className="bg-gray-800 rounded-2xl p-5">
              <h2 className="font-bold text-white mb-3 flex items-center gap-2 text-sm">
                <Info className="w-4 h-4 text-cyan-400" />
                {t('results.structures.dimensions')}
              </h2>
              <div className="flex flex-wrap gap-2">
                {Object.entries(structure.dimensions).map(([k, v]) => (
                  <span
                    key={k}
                    className="text-[11px] bg-gray-700 text-gray-200 px-2.5 py-1 rounded-lg"
                  >
                    {k.replace(/_/g, ' ')}: <strong>{String(v)}</strong>
                  </span>
                ))}
              </div>
              <p className="text-[11px] text-gray-500 mt-3">
                {t('ar.scaleNote')}
              </p>
            </div>
          )}

          {/* assessment summary */}
          {data && (
            <div className="bg-gray-800 rounded-2xl p-5">
              <h2 className="font-bold text-white mb-3 text-sm">
                {t('ar.yourAssessment')}
              </h2>
              <div className="space-y-2 text-sm">
                <Row
                  label={t('ar.roofArea')}
                  value={`${data.request.roof_area} m²`}
                />
                <Row
                  label={t('ar.annualRunoff')}
                  value={formatLiters(data.runoff.annual_runoff_volume)}
                  accent
                />
                <Row
                  label={t('ar.topStructure')}
                  value={structureLabel(
                    data.recommended_structures[0]?.structure_type ?? '—',
                  )}
                />
              </div>
            </div>
          )}

          <Link
            href="/results"
            className="block w-full text-center bg-primary-700 hover:bg-primary-800 text-white font-bold py-3 rounded-xl transition-colors"
          >
            {t('ar.back')}
          </Link>
        </div>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-gray-400 text-xs">{label}</span>
      <span
        className={`font-bold text-xs text-right ${
          accent ? 'text-cyan-400' : 'text-white'
        }`}
      >
        {value}
      </span>
    </div>
  );
}
