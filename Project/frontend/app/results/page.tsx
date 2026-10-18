'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import {
  Download,
  RefreshCw,
  Camera,
  Info,
  AlertTriangle,
} from 'lucide-react';

import type { AssessmentResponse } from '@/lib/types';
import { formatLiters, formatINR, MONTHS } from '@/lib/utils';
import { downloadReport, getAssessment } from '@/lib/api';
import { useI18n, type TranslationKey } from '@/lib/i18n';

/* ============================================================
   SMALL PIECES
============================================================ */

function MetricCard({
  label,
  value,
  sub,
  icon,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  icon: string;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl p-5 ${color} flex flex-col gap-2`}
    >
      <div className="text-2xl">{icon}</div>
      <div className="text-2xl font-extrabold text-gray-800 font-numeric">
        {value}
      </div>
      <div className="text-sm font-semibold text-gray-700">{label}</div>
      <div className="text-xs text-gray-500">{sub}</div>
    </motion.div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 70 ? 'bg-green-500' : score >= 40 ? 'bg-yellow-500' : 'bg-red-400';
  return (
    <div className="w-full bg-gray-100 rounded-full h-3">
      <div
        className={`${color} h-3 rounded-full transition-all duration-1000`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 border-b border-gray-50">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="font-semibold text-gray-800 text-sm text-right font-numeric">
        {value}
      </span>
    </div>
  );
}

/** Payback is nullable: "never" must not render as a real number. */
function PaybackText({ years }: { years: number | null }) {
  const { t } = useI18n();
  if (years === null) return <>{t('results.cb.notViable')}</>;
  return <>{years} {t('common.years')}</>;
}

/* ============================================================
   MAIN
============================================================ */

function ResultsContent() {
  const router = useRouter();
  const params = useSearchParams();
  const { t, structureLabel, soilLabel, roofLabel } = useI18n();

  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [downloading, setDownloading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const assessmentId = params?.get('id');

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const stored = localStorage.getItem('hydro_result');

      if (stored) {
        try {
          const parsed = JSON.parse(stored) as AssessmentResponse;
          // Honour a shared link over whatever this browser last saved.
          if (!assessmentId || parsed.assessment_id === assessmentId) {
            setData(parsed);
            return;
          }
        } catch {
          /* corrupt blob — fall through to the API */
        }
      }

      if (assessmentId) {
        try {
          const fetched = await getAssessment(assessmentId);
          if (!cancelled) {
            setData(fetched);
            localStorage.setItem('hydro_result', JSON.stringify(fetched));
          }
          return;
        } catch {
          if (!cancelled) setLoadError(t('assess.error.backend'));
          return;
        }
      }

      if (!cancelled) router.push('/assess');
    };

    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId, router]);

  const handleDownload = useCallback(async () => {
    if (!data) return;
    setDownloading(true);
    try {
      await downloadReport(data.assessment_id);
    } catch {
      alert(t('assess.error.backend'));
    } finally {
      setDownloading(false);
    }
  }, [data, t]);

  /* ---------- loading / error ---------- */

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-4" />
          <p className="text-gray-700 mb-6">{loadError}</p>
          <Link
            href="/assess"
            className="inline-block bg-primary-700 text-white font-bold px-6 py-3 rounded-xl"
          >
            {t('results.new')}
          </Link>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-700 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">{t('results.loading')}</p>
        </div>
      </div>
    );
  }

  /* ---------- data ---------- */

  const {
    runoff,
    recharge,
    weather,
    cost_benefit: cb,
    recommended_structures,
    hydrogeo_info: hg,
    request,
  } = data;

  const monthlyChartData = MONTHS.map((m, i) => ({
    month: m,
    rainfall: Math.round(weather.monthly_rainfall[i]),
    runoff: Math.round((runoff.monthly_runoff[i] / 1000) * 10) / 10,
    savings: Math.round(cb.monthly_savings[i]),
  }));

  const tabs: { id: string; labelKey: TranslationKey }[] = [
    { id: 'overview', labelKey: 'results.tab.overview' },
    { id: 'monthly', labelKey: 'results.tab.monthly' },
    { id: 'structures', labelKey: 'results.tab.structures' },
    { id: 'costbenefit', labelKey: 'results.tab.costbenefit' },
    { id: 'hydrogeo', labelKey: 'results.tab.hydrogeo' },
  ];

  const paybackText =
    cb.payback_period_years === null ? null : cb.payback_period_years;

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* ---- header ---- */}
      <div className="gradient-water text-white py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-blue-200 text-sm mb-1 font-numeric">
                {t('results.assessmentId')}: {data.assessment_id}
              </p>
              <h1 className="text-2xl sm:text-3xl font-bold">
                {t('results.title')}
              </h1>
              <p className="text-blue-100 mt-1">
                {request.name} • {request.location}
              </p>
              <p className="text-blue-200 text-xs mt-1">
                {request.roof_area}m² {roofLabel(request.roof_type)} •{' '}
                {request.num_people} • {weather.location_name}
              </p>
            </div>

            <div className="flex gap-3 flex-wrap">
              <Link
                href="/ar"
                className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-4 py-2.5 rounded-xl font-semibold text-sm transition-all"
              >
                <Camera className="w-4 h-4" />
                {t('results.arView')}
              </Link>

              <button
                onClick={handleDownload}
                disabled={downloading}
                className="flex items-center gap-2 bg-white text-primary-700 px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-blue-50 transition-all disabled:opacity-70"
              >
                <Download className="w-4 h-4" />
                {downloading ? t('results.downloading') : t('results.download')}
              </button>

              <Link
                href="/assess"
                className="flex items-center gap-2 bg-secondary-500 text-white px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-secondary-600 transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                {t('results.new')}
              </Link>
            </div>
          </div>

          {/* ---- summary cards ---- */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <MetricCard
              label={t('results.metric.runoff')}
              value={formatLiters(runoff.annual_runoff_volume)}
              sub={`${t('results.metric.harvestable')}: ${formatLiters(
                runoff.harvestable_volume,
              )}`}
              icon="💧"
              color="bg-blue-50"
            />
            <MetricCard
              label={t('results.metric.recharge')}
              value={formatLiters(recharge.annual_recharge_potential)}
              sub={`${recharge.groundwater_recharge_rate.toFixed(1)} L/day`}
              icon="🌊"
              color="bg-cyan-50"
            />
            <MetricCard
              label={t('results.metric.savings')}
              value={formatINR(cb.annual_savings_inr)}
              sub={`${t('results.metric.payback')}: ${
                paybackText === null
                  ? t('results.cb.notViable')
                  : `${paybackText} ${t('common.years')}`
              }`}
              icon="💰"
              color="bg-green-50"
            />
            <MetricCard
              label={t('results.metric.feasibility')}
              value={`${recharge.recharge_feasibility_score}/100`}
              sub={recharge.aquifer_type}
              icon="🎯"
              color="bg-purple-50"
            />
          </div>
        </div>
      </div>

      {/* ---- tabs ---- */}
      <div className="max-w-6xl mx-auto px-4 mt-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-700 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {t(tab.labelKey)}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {/* ================= OVERVIEW ================= */}
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              <Panel title={`☁️ ${t('results.overview.weather')}`}>
                <StatRow
                  label={t('results.key.location')}
                  value={weather.location_name}
                />
                <StatRow
                  label={t('results.key.annualRainfall')}
                  value={`${weather.annual_rainfall} ${t('common.mm')}`}
                />
                <StatRow
                  label={t('results.key.temperature')}
                  value={`${weather.avg_temperature}°C`}
                />
                <StatRow
                  label={t('results.key.humidity')}
                  value={`${weather.humidity}%`}
                />
              </Panel>

              <Panel title={`🏠 ${t('results.overview.runoffSummary')}`}>
                <StatRow
                  label={t('results.key.runoffCoeff')}
                  value={runoff.runoff_coefficient.toString()}
                />
                <StatRow
                  label={t('results.key.annualRunoff')}
                  value={formatLiters(runoff.annual_runoff_volume)}
                />
                <StatRow
                  label={t('results.key.afterFirstFlush')}
                  value={formatLiters(runoff.harvestable_volume)}
                />
                <StatRow
                  label={t('results.key.peakRunoff')}
                  value={`${runoff.peak_runoff_rate.toFixed(4)} m³/hr`}
                />
                <StatRow
                  label={t('results.key.roofType')}
                  value={roofLabel(request.roof_type)}
                />
              </Panel>

              <Panel title={`🌊 ${t('results.overview.rechargeSummary')}`}>
                <StatRow
                  label={t('results.key.aquiferType')}
                  value={recharge.aquifer_type}
                />
                <StatRow
                  label={t('results.key.infiltration')}
                  value={`${recharge.infiltration_rate} mm/hr`}
                />
                <StatRow
                  label={t('results.key.annualRecharge')}
                  value={formatLiters(recharge.annual_recharge_potential)}
                />
                <StatRow
                  label={t('results.key.dailyRecharge')}
                  value={`${recharge.groundwater_recharge_rate.toFixed(1)} L/day`}
                />
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">
                      {t('results.key.feasibilityScore')}
                    </span>
                    <span className="font-bold text-primary-700 font-numeric">
                      {recharge.recharge_feasibility_score}/100
                    </span>
                  </div>
                  <ScoreBar score={recharge.recharge_feasibility_score} />
                </div>
              </Panel>

              <Panel title={`🏗️ ${t('results.overview.topReco')}`}>
                {recommended_structures[0] && (
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center text-lg">
                        🏗️
                      </div>
                      <div>
                        <p className="font-bold text-gray-800">
                          {structureLabel(
                            recommended_structures[0].structure_type,
                          )}
                        </p>
                        <p className="text-xs text-gray-500 font-numeric">
                          {t('results.key.score')}:{' '}
                          {recommended_structures[0].suitability_score}/100
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {recommended_structures[0].description}
                    </p>
                    <div className="mt-3">
                      <ScoreBar
                        score={recommended_structures[0].suitability_score}
                      />
                    </div>
                  </div>
                )}
              </Panel>
            </motion.div>
          )}

          {/* ================= MONTHLY ================= */}
          {activeTab === 'monthly' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">
                  {t('results.monthly.chartTitle')}
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 12 }}
                      label={{
                        value: `${t('results.monthly.rainfall')} (${t('common.mm')})`,
                        angle: 90,
                        position: 'insideLeft',
                        style: { fontSize: 11 },
                      }}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12 }}
                      label={{
                        value: `${t('results.monthly.runoff')} (KL)`,
                        angle: 90,
                        position: 'insideRight',
                        offset: 5,
                        style: { fontSize: 11 },
                      }}
                    />
                    <Tooltip />
                    <Legend />
                    <Bar
                      yAxisId="left"
                      dataKey="rainfall"
                      fill="#0d5c8c"
                      name={`${t('results.monthly.rainfall')} (${t('common.mm')})`}
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      yAxisId="right"
                      dataKey="runoff"
                      fill="#27ae60"
                      name={`${t('results.monthly.runoff')} (KL)`}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">
                  {t('results.monthly.savingsTitle')}
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="savings"
                      stroke="#27ae60"
                      fill="#d4edda"
                      name={t('results.monthly.savings')}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          )}

          {/* ================= STRUCTURES ================= */}
          {activeTab === 'structures' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              {recommended_structures.map((s, i) => (
                <div
                  key={i}
                  className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100"
                >
                  <div className="flex items-start justify-between mb-3 gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-xl flex items-center justify-center font-bold text-lg font-numeric">
                        {i + 1}
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-800">
                          {structureLabel(s.structure_type)}
                        </h3>
                        <p className="text-xs text-gray-400 font-numeric">
                          {t('results.key.suitability')}:{' '}
                          {s.suitability_score}/100
                        </p>
                      </div>
                    </div>
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ${
                        s.suitability_score >= 70
                          ? 'bg-green-100 text-green-700'
                          : s.suitability_score >= 40
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {s.suitability_score >= 70
                        ? t('results.structures.highly')
                        : s.suitability_score >= 40
                        ? t('results.structures.suitable')
                        : t('results.structures.marginal')}
                    </span>
                  </div>

                  <ScoreBar score={s.suitability_score} />

                  <p className="text-sm text-gray-600 mt-4 leading-relaxed">
                    {s.description}
                  </p>

                  <div className="mt-3 bg-blue-50 rounded-xl p-3">
                    <p className="text-xs font-semibold text-primary-700 mb-1">
                      📐 {t('results.structures.dimensions')}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(s.dimensions).map(([k, v]) => (
                        <span
                          key={k}
                          className="text-xs bg-white border border-blue-100 px-2 py-1 rounded-lg text-gray-700 font-numeric"
                        >
                          {k.replace(/_/g, ' ')}: <strong>{String(v)}</strong>
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-3 bg-green-50 rounded-xl p-3">
                    <p className="text-xs font-semibold text-green-700 mb-1">
                      🔧 {t('results.structures.installation')}
                    </p>
                    <p className="text-xs text-gray-600">{s.installation_notes}</p>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* ================= COST BENEFIT ================= */}
          {activeTab === 'costbenefit' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MiniCard
                  label={t('results.cb.installation')}
                  value={formatINR(cb.estimated_cost)}
                  icon="🏗️"
                  color="bg-orange-50"
                />
                <MiniCard
                  label={t('results.cb.annualSavings')}
                  value={formatINR(cb.annual_savings_inr)}
                  icon="💰"
                  color="bg-green-50"
                />
                <MiniCard
                  label={t('results.cb.payback')}
                  value={
                    paybackText === null
                      ? t('results.cb.notViable')
                      : `${paybackText} ${t('common.years')}`
                  }
                  icon="📅"
                  color="bg-blue-50"
                />
                <MiniCard
                  label={t('results.cb.roi')}
                  value={`${cb.roi_percentage}%`}
                  icon="📈"
                  color="bg-purple-50"
                />
              </div>

              {!cb.economically_viable && (
                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-sm text-amber-800 leading-relaxed">
                    {t('results.cb.notViableNote')}
                  </p>
                </div>
              )}

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">
                  {t('results.cb.breakdownTitle')}
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="savings"
                      fill="#27ae60"
                      name={t('results.monthly.savings')}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">
                  {t('results.cb.summaryTitle')}
                </h3>
                <StatRow
                  label={t('results.cb.totalCost')}
                  value={formatINR(cb.estimated_cost)}
                />
                <StatRow
                  label={`↳ ${t('results.cb.storage')}`}
                  value={formatINR(cb.storage_cost)}
                />
                <StatRow
                  label={`↳ ${t('results.cb.recharge')}`}
                  value={formatINR(cb.recharge_cost)}
                />
                <StatRow
                  label={`↳ ${t('results.cb.plumbing')}`}
                  value={formatINR(cb.plumbing_cost)}
                />
                <StatRow
                  label={t('results.cb.waterSaved')}
                  value={formatLiters(cb.annual_water_savings_liters)}
                />
                <StatRow
                  label={t('results.cb.annualSavings')}
                  value={formatINR(cb.annual_savings_inr)}
                />
                <StatRow
                  label={t('results.cb.rechargeValue')}
                  value={formatINR(cb.annual_recharge_value_inr)}
                />
                <StatRow
                  label={t('results.cb.maintenance')}
                  value={formatINR(cb.annual_maintenance_inr)}
                />
                <StatRow
                  label={t('results.cb.netSavings')}
                  value={formatINR(cb.net_annual_savings_inr)}
                />
                <StatRow
                  label={t('results.cb.tariff')}
                  value={`${formatINR(cb.water_tariff_per_kl)} / KL`}
                />
                <StatRow
                  label={t('results.cb.simplePayback')}
                  value={
                    paybackText === null
                      ? t('results.cb.notViable')
                      : `${paybackText} ${t('common.years')}`
                  }
                />
                <StatRow
                  label={t('results.cb.roi10')}
                  value={`${cb.roi_percentage}%`}
                />
              </div>
            </motion.div>
          )}

          {/* ================= HYDROGEOLOGY ================= */}
          {activeTab === 'hydrogeo' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">
                  🌊 {t('results.hydro.title')}
                </h3>
                <StatRow
                  label={t('results.hydro.aquiferType')}
                  value={hg.aquifer_type}
                />
                <StatRow
                  label={t('results.hydro.aquiferDepth')}
                  value={`${hg.aquifer_depth} m`}
                />
                <StatRow
                  label={t('results.hydro.permeability')}
                  value={hg.permeability}
                />
                <StatRow
                  label={t('results.hydro.storageCoeff')}
                  value={hg.storage_coefficient.toString()}
                />
                <StatRow
                  label={t('results.hydro.transmissivity')}
                  value={`${hg.transmissivity.toFixed(1)} m²/day`}
                />
                <StatRow
                  label={t('results.hydro.quality')}
                  value={hg.groundwater_quality}
                />
                <StatRow
                  label={t('results.hydro.fluctuation')}
                  value={`${hg.seasonal_fluctuation} m`}
                />
                <StatRow
                  label={t('results.hydro.soilType')}
                  value={soilLabel(request.soil_type)}
                />
                <StatRow
                  label={t('results.hydro.openSpace')}
                  value={`${request.open_space_area} m²`}
                />
              </div>

              <div className="bg-blue-50 rounded-2xl p-5 border border-blue-100">
                <div className="flex gap-3">
                  <Info className="w-5 h-5 text-primary-700 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-primary-700 text-sm">
                      {t('results.hydro.aboutTitle')}
                    </p>
                    <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                      {t('results.hydro.aboutBody')}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   PANELS
============================================================ */

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="font-bold text-gray-800 mb-4">{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function MiniCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: string;
  color: string;
}) {
  return (
    <div className={`${color} rounded-2xl p-4 text-center`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-lg font-extrabold text-gray-800 font-numeric">
        {value}
      </div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

/* ============================================================
   EXPORT
============================================================ */

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-4 border-primary-700 border-t-transparent rounded-full" />
        </div>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}
