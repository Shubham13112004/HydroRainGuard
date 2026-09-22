'use client';
import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, AreaChart, Area
} from 'recharts';
import { Download, RefreshCw, Camera, Droplets, TrendingUp, Award, Info } from 'lucide-react';
import type { AssessmentResponse } from '@/lib/types';
import { formatLiters, formatINR, MONTHS } from '@/lib/utils';
import { downloadReport } from '@/lib/api';

function MetricCard({ label, value, sub, icon, color }: { label: string; value: string; sub: string; icon: string; color: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl p-5 ${color} flex flex-col gap-2`}
    >
      <div className="text-2xl">{icon}</div>
      <div className="text-2xl font-extrabold text-gray-800">{value}</div>
      <div className="text-sm font-semibold text-gray-700">{label}</div>
      <div className="text-xs text-gray-500">{sub}</div>
    </motion.div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? 'bg-green-500' : score >= 40 ? 'bg-yellow-500' : 'bg-red-400';
  return (
    <div className="w-full bg-gray-100 rounded-full h-3">
      <div className={`${color} h-3 rounded-full transition-all duration-1000`} style={{ width: `${score}%` }} />
    </div>
  );
}

function ResultsContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('hydro_result');
    if (stored) {
      setData(JSON.parse(stored));
    } else {
      router.push('/assess');
    }
  }, [router]);

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-700 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading results...</p>
        </div>
      </div>
    );
  }

  const { runoff, recharge, weather, cost_benefit, recommended_structures, hydrogeo_info, request, assessment_id } = data;

  const monthlyChartData = MONTHS.map((m, i) => ({
    month: m,
    rainfall: Math.round(weather.monthly_rainfall[i]),
    runoff: Math.round(runoff.monthly_runoff[i] / 1000 * 10) / 10,
    savings: Math.round(cost_benefit.monthly_savings[i]),
  }));

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadReport(assessment_id);
    } catch {
      alert('Failed to download. Make sure the backend is running.');
    } finally {
      setDownloading(false);
    }
  };

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'monthly', label: '📈 Monthly Analysis' },
    { id: 'structures', label: '🏗️ Structures' },
    { id: 'costbenefit', label: '💰 Cost-Benefit' },
    { id: 'hydrogeo', label: '🌊 Hydrogeology' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Header */}
      <div className="gradient-water text-white py-10 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-blue-200 text-sm mb-1">Assessment ID: {assessment_id}</p>
              <h1 className="text-3xl font-bold">Assessment Results</h1>
              <p className="text-blue-100 mt-1">{request.name} • {request.location}</p>
              <p className="text-blue-200 text-xs mt-1">{request.roof_area}m² {request.roof_type} roof • {request.num_people} people • {weather.location_name}</p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <Link href="/ar" className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-4 py-2.5 rounded-xl font-semibold text-sm transition-all">
                <Camera className="w-4 h-4" /> AR View
              </Link>
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="flex items-center gap-2 bg-white text-primary-700 px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-blue-50 transition-all disabled:opacity-70"
              >
                <Download className="w-4 h-4" /> {downloading ? 'Generating...' : 'Download PDF'}
              </button>
              <Link href="/assess" className="flex items-center gap-2 bg-secondary-500 text-white px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-secondary-600 transition-all">
                <RefreshCw className="w-4 h-4" /> New Assessment
              </Link>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <MetricCard label="Annual Runoff" value={formatLiters(runoff.annual_runoff_volume)} sub={`Harvestable: ${formatLiters(runoff.harvestable_volume)}`} icon="💧" color="bg-blue-50" />
            <MetricCard label="Recharge Potential" value={formatLiters(recharge.annual_recharge_potential)} sub={`${recharge.groundwater_recharge_rate.toFixed(1)} L/day`} icon="🌊" color="bg-cyan-50" />
            <MetricCard label="Annual Savings" value={formatINR(cost_benefit.annual_savings_inr)} sub={`Payback: ${cost_benefit.payback_period_years} years`} icon="💰" color="bg-green-50" />
            <MetricCard label="Feasibility Score" value={`${recharge.recharge_feasibility_score}/100`} sub={recharge.aquifer_type} icon="🎯" color="bg-purple-50" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto px-4 mt-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all ${
                activeTab === t.id
                  ? 'bg-primary-700 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="mt-6">
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">☁️ Weather & Rainfall</h3>
                <div className="space-y-3">
                  {[['Location', weather.location_name],['Annual Rainfall', `${weather.annual_rainfall} mm`],['Avg Temperature', `${weather.avg_temperature}°C`],['Humidity', `${weather.humidity}%`]].map(([k,v]) => (
                    <div key={k} className="flex justify-between items-center py-2 border-b border-gray-50">
                      <span className="text-sm text-gray-500">{k}</span>
                      <span className="font-semibold text-gray-800 text-sm">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">🏠 Runoff Summary</h3>
                <div className="space-y-3">
                  {[
                    ['Runoff Coefficient (C)', runoff.runoff_coefficient.toString()],
                    ['Annual Runoff Volume', formatLiters(runoff.annual_runoff_volume)],
                    ['After First-Flush Loss', formatLiters(runoff.harvestable_volume)],
                    ['Peak Runoff Rate', `${runoff.peak_runoff_rate.toFixed(4)} m³/hr`],
                    ['Roof Area', `${request.roof_area} m²`],
                    ['Roof Type', request.roof_type],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between items-center py-2 border-b border-gray-50">
                      <span className="text-sm text-gray-500">{k}</span>
                      <span className="font-semibold text-gray-800 text-sm">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">🌊 Recharge Summary</h3>
                <div className="space-y-3">
                  {[
                    ['Aquifer Type', recharge.aquifer_type],
                    ['Infiltration Rate', `${recharge.infiltration_rate} mm/hr`],
                    ['Annual Recharge', formatLiters(recharge.annual_recharge_potential)],
                    ['Daily Recharge Rate', `${recharge.groundwater_recharge_rate.toFixed(1)} L/day`],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between items-center py-2 border-b border-gray-50">
                      <span className="text-sm text-gray-500">{k}</span>
                      <span className="font-semibold text-gray-800 text-sm">{v}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">Feasibility Score</span>
                    <span className="font-bold text-primary-700">{recharge.recharge_feasibility_score}/100</span>
                  </div>
                  <ScoreBar score={recharge.recharge_feasibility_score} />
                </div>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">🏗️ Top Recommendation</h3>
                {recommended_structures[0] && (
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center text-lg">🏗️</div>
                      <div>
                        <p className="font-bold text-gray-800">{recommended_structures[0].structure_type}</p>
                        <p className="text-xs text-gray-500">Score: {recommended_structures[0].suitability_score}/100</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">{recommended_structures[0].description}</p>
                    <ScoreBar score={recommended_structures[0].suitability_score} />
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* MONTHLY ANALYSIS TAB */}
          {activeTab === 'monthly' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">Monthly Rainfall vs Rooftop Runoff</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={monthlyChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 12 }} label={{ value: 'Rainfall (mm)', angle: -90, position: 'insideLeft', offset: -5, style: { fontSize: 11 } }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} label={{ value: 'Runoff (KL)', angle: 90, position: 'insideRight', offset: 5, style: { fontSize: 11 } }} />
                    <Tooltip formatter={(val, name) => [name === 'rainfall' ? `${val} mm` : `${val} KL`, name === 'rainfall' ? 'Rainfall' : 'Runoff']} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="rainfall" fill="#0d5c8c" name="Rainfall (mm)" radius={[4,4,0,0]} />
                    <Bar yAxisId="right" dataKey="runoff" fill="#27ae60" name="Runoff (KL)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">Monthly Water Cost Savings (₹)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(val) => [`₹${val}`, 'Monthly Savings']} />
                    <Area type="monotone" dataKey="savings" stroke="#27ae60" fill="#d4edda" name="Savings (₹)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          )}

          {/* STRUCTURES TAB */}
          {activeTab === 'structures' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              {recommended_structures.map((s, i) => (
                <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 text-primary-700 rounded-xl flex items-center justify-center font-bold text-lg">{i+1}</div>
                      <div>
                        <h3 className="font-bold text-gray-800">{s.structure_type}</h3>
                        <p className="text-xs text-gray-400">Suitability: {s.suitability_score}/100</p>
                      </div>
                    </div>
                    <div className={`text-xs font-bold px-3 py-1 rounded-full ${
                      s.suitability_score >= 70 ? 'bg-green-100 text-green-700' :
                      s.suitability_score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {s.suitability_score >= 70 ? 'Highly Suitable' : s.suitability_score >= 40 ? 'Suitable' : 'Marginal'}
                    </div>
                  </div>
                  <ScoreBar score={s.suitability_score} />
                  <p className="text-sm text-gray-600 mt-4 leading-relaxed">{s.description}</p>
                  <div className="mt-3 bg-blue-50 rounded-xl p-3">
                    <p className="text-xs font-semibold text-primary-700 mb-1">📐 Dimensions</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(s.dimensions).map(([k,v]) => (
                        <span key={k} className="text-xs bg-white border border-blue-100 px-2 py-1 rounded-lg text-gray-700">
                          {k.replace(/_/g,' ')}: <strong>{v}</strong>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="mt-3 bg-green-50 rounded-xl p-3">
                    <p className="text-xs font-semibold text-green-700 mb-1">🔧 Installation Notes</p>
                    <p className="text-xs text-gray-600">{s.installation_notes}</p>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* COST-BENEFIT TAB */}
          {activeTab === 'costbenefit' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[{
                  label: 'Installation Cost', value: formatINR(cost_benefit.estimated_cost), icon: '🏗️', color: 'bg-orange-50'
                },{
                  label: 'Annual Savings', value: formatINR(cost_benefit.annual_savings_inr), icon: '💰', color: 'bg-green-50'
                },{
                  label: 'Payback Period', value: `${cost_benefit.payback_period_years} yrs`, icon: '📅', color: 'bg-blue-50'
                },{
                  label: '10-Year ROI', value: `${cost_benefit.roi_percentage}%`, icon: '📈', color: 'bg-purple-50'
                }].map((c,i) => (
                  <div key={i} className={`${c.color} rounded-2xl p-4 text-center`}>
                    <div className="text-2xl mb-1">{c.icon}</div>
                    <div className="text-xl font-extrabold text-gray-800">{c.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{c.label}</div>
                  </div>
                ))}
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-6">Monthly Cost Savings Breakdown (₹)</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(val) => [`₹${val}`, 'Savings']} />
                    <Bar dataKey="savings" fill="#27ae60" name="Monthly Savings (₹)" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">Financial Summary</h3>
                <div className="space-y-2">
                  {[
                    ['Total Installation Cost', formatINR(cost_benefit.estimated_cost)],
                    ['Water Saved per Year', formatLiters(cost_benefit.annual_water_savings_liters)],
                    ['Gross Annual Savings', formatINR(cost_benefit.annual_savings_inr)],
                    ['Annual Maintenance (2%)', formatINR(cost_benefit.estimated_cost * 0.02)],
                    ['Net Annual Savings', formatINR(cost_benefit.annual_savings_inr - cost_benefit.estimated_cost * 0.02)],
                    ['Simple Payback Period', `${cost_benefit.payback_period_years} years`],
                    ['10-Year Return on Investment', `${cost_benefit.roi_percentage}%`],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between py-2.5 border-b border-gray-50">
                      <span className="text-sm text-gray-500">{k}</span>
                      <span className="font-bold text-gray-800 text-sm">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* HYDROGEOLOGY TAB */}
          {activeTab === 'hydrogeo' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-800 mb-4">🌊 Hydrogeological Information</h3>
                <div className="space-y-3">
                  {[
                    ['Aquifer Type', hydrogeo_info.aquifer_type],
                    ['Aquifer Depth', `${hydrogeo_info.aquifer_depth} m`],
                    ['Soil Permeability', hydrogeo_info.permeability],
                    ['Storage Coefficient', hydrogeo_info.storage_coefficient.toString()],
                    ['Transmissivity', `${hydrogeo_info.transmissivity.toFixed(1)} m²/day`],
                    ['Groundwater Quality', hydrogeo_info.groundwater_quality],
                    ['Seasonal Water Table Fluctuation', `${hydrogeo_info.seasonal_fluctuation} m`],
                    ['Soil Type', request.soil_type],
                    ['Open Space Area', `${request.open_space_area} m²`],
                  ].map(([k,v]) => (
                    <div key={k} className="flex justify-between py-2.5 border-b border-gray-50">
                      <span className="text-sm text-gray-500">{k}</span>
                      <span className="font-semibold text-gray-800 text-sm">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-blue-50 rounded-2xl p-5 border border-blue-100">
                <div className="flex gap-3">
                  <Info className="w-5 h-5 text-primary-700 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-primary-700 text-sm">About the Aquifer Assessment</p>
                    <p className="text-xs text-gray-600 mt-1 leading-relaxed">Aquifer type is estimated based on groundwater depth and soil characteristics. For precise aquifer mapping, refer to CGWB district groundwater atlases or BHUVAN GIS portal. Seasonal fluctuation is estimated from annual rainfall data.</p>
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

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin w-8 h-8 border-4 border-primary-700 border-t-transparent rounded-full"/></div>}>
      <ResultsContent />
    </Suspense>
  );
}
