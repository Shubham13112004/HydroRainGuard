'use client';

import { useI18n, type TranslationKey } from '@/lib/i18n';

type Member = { name: string; roleKey: TranslationKey };

export default function AboutPage() {
  const { t } = useI18n();

  const team: Member[] = [
    { name: 'Dr. Dipali Patil', roleKey: 'about.role.pi' },
    { name: 'Shubham Desai', roleKey: 'about.role.hydro' },
    { name: 'Siddhesh Mahadik', roleKey: 'about.role.gis' },
    { name: 'Kaushal Agale', roleKey: 'about.role.ai' },
    { name: 'Omkar Kshirsagar', roleKey: 'about.role.ar' },
  ];

  const refs = [
    '[1] CGWB, Manual on Artificial Recharge of Groundwater, 2007.',
    '[2] BIS, Guidelines for Rainwater Harvesting, IS 15797, 2008.',
    '[3] Lu et al., "Evaluating the impact of roof rainwater harvesting," Results in Engineering, vol. 25, 2025.',
    '[4] Doorn, "Artificial intelligence in the water domain," Science of the Total Environment, vol. 755, 2021.',
    '[5] Preeti & Rahman, "Application of GIS in rainwater harvesting research," Asian J. Water Env. Pollution, 2021.',
    '[6] Ali et al., "Implementing urban rainwater harvesting systems," Renewable & Sustainable Energy Reviews, vol. 218, 2025.',
    '[7] Mane & Patil, "Review on rooftop rainwater harvesting in Nimgaon Village," IJERT, vol. 10, 2021.',
    '[8] Deshmukh et al., "Recent trends in rooftop rainwater harvesting technologies," IJRASET, vol. 10, 2022.',
    '[9] CEEW, Rainwater Harvesting: Artificial Recharge of Groundwater in India, 2023.',
    '[10] IMD, Yearly Gridded Rainfall Data, 2024.',
    '[11] Hari & Kasa, "Geospatial approach for rooftop rainwater harvesting potential assessment," Grassroots J., 2025.',
    '[12] "Design and analysis of rooftop rainwater harvesting with borewell recharge," IRJMETS, 2025.',
    '[13] Hansen et al., "Augmented reality for subsurface utility engineering," IEEE TVCG, vol. 27, 2021.',
    '[14] NOAA PSL, CPC Merged Analysis of Precipitation (CMAP) monthly long-term means, 1991–2020. Public domain.',
    '[15] USDA-NRCS, Urban Hydrology for Small Watersheds, TR-55, 1986 — SCS Curve Number method.',
    '[16] Saaty T.L., The Analytic Hierarchy Process, McGraw-Hill, 1980.',
    '[17] Xie & Arkin, "Global precipitation: a 17-year monthly analysis based on gauge observations, satellite estimates and numerical model outputs," J. Climate, 1997 — the CMAP method.',
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="gradient-water text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-5xl mb-4">💧</div>
          <h1 className="text-4xl font-extrabold mb-3">{t('about.title')}</h1>
          <p className="text-blue-100 text-lg">{t('about.subtitle')}</p>
          <div className="flex flex-wrap gap-3 justify-center mt-4">
            <span className="bg-white/20 px-3 py-1 rounded-full text-sm">Paper ID: 195</span>
            <span className="bg-white/20 px-3 py-1 rounded-full text-sm">ICICIS Conference 2026 — ADYPU</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-12 space-y-10">
        {/* Institution */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-3">🏛️ {t('about.institution')}</h2>
          <p className="text-gray-600">{t('about.institutionBody')}</p>
          <p className="text-gray-500 text-sm mt-1">{t('about.presented')}</p>
        </div>

        {/* Team */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-4">👥 {t('about.team')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {team.map((m, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-blue-50 rounded-xl">
                <div className="w-10 h-10 bg-primary-700 text-white rounded-full flex items-center justify-center font-bold text-sm">
                  {m.name.split(' ').map(w => w[0]).join('')}
                </div>
                <div>
                  <p className="font-semibold text-gray-800 text-sm">{m.name}</p>
                  <p className="text-xs text-gray-500">{t(m.roleKey)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Framework */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-3">🎯 {t('about.objectives')}</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-600 text-sm">
            <li>Review hydrological modelling techniques for runoff estimation and groundwater recharge assessment.</li>
            <li>Analyze GIS and remote sensing applications for recharge planning.</li>
            <li>Investigate AI-based prediction and recommendation techniques.</li>
            <li>Identify research trends, technological gaps, and integration opportunities.</li>
            <li>Propose the HYDRO RAIN GUARD conceptual framework.</li>
            <li>Identify research gaps and relate them to the proposed framework.</li>
          </ol>
        </div>

        {/* What is actually implemented */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-3">
            ✅ Implemented in this build
          </h2>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>
              <strong className="text-gray-800">Gridded rainfall (GIS).</strong>{' '}
              NOAA PSL CMAP 2.5° monthly climatology (1991–2020), bilinearly
              interpolated to your exact coordinates — real gauge + satellite
              data, public domain, no API key.
            </li>
            <li>
              <strong className="text-gray-800">Two runoff methods.</strong>{' '}
              Rational/volumetric (CGWB 2007) for the result, SCS Curve Number
              (USDA-NRCS TR-55) reported alongside as a cross-check.
            </li>
            <li>
              <strong className="text-gray-800">Structure ranking.</strong>{' '}
              Analytic Hierarchy Process (Saaty, 1980) — weighted,
              consistency-checked (CR = 0.015) multi-criteria scoring.
              Deterministic and auditable; <em>not</em> machine learning.
            </li>
            <li>
              <strong className="text-gray-800">Multi-script PDF.</strong>{' '}
              HarfBuzz shaping renders English, हिन्दी and मराठी correctly —
              conjuncts, half-forms and matra placement included.
            </li>
            <li>
              <strong className="text-gray-800">3D / AR preview</strong> of the
              recommended structures, sized from your own assessment data.
            </li>
          </ul>
        </div>

        {/* Technology Stack */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-4">⚙️ {t('about.techStack')}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { name: 'Python', color: 'bg-yellow-100 text-yellow-800', emoji: '🐍' },
              { name: 'FastAPI', color: 'bg-green-100 text-green-800', emoji: '⚡' },
              { name: 'Next.js', color: 'bg-gray-100 text-gray-800', emoji: '▲' },
              { name: 'SQLite/PostgreSQL', color: 'bg-blue-100 text-blue-800', emoji: '🗄️' },
              { name: 'Recharts', color: 'bg-purple-100 text-purple-800', emoji: '📊' },
              { name: 'React Three Fiber (3D/AR)', color: 'bg-orange-100 text-orange-800', emoji: '🥽' },
              { name: 'OpenWeatherMap (optional)', color: 'bg-cyan-100 text-cyan-800', emoji: '🌤️' },
              { name: 'ReportLab', color: 'bg-red-100 text-red-800', emoji: '📄' },
              { name: 'NOAA CMAP gridded rainfall', color: 'bg-blue-100 text-blue-800', emoji: '🌧️' },
              { name: 'HarfBuzz + fontTools', color: 'bg-indigo-100 text-indigo-800', emoji: '🔤' },
              { name: 'AHP decision engine', color: 'bg-teal-100 text-teal-800', emoji: '⚖️' },
              { name: 'Leaflet / OpenStreetMap', color: 'bg-emerald-100 text-emerald-800', emoji: '🗺️' },
            ].map((tech, i) => (
              <div key={i} className={`${tech.color} rounded-xl px-3 py-2 text-center`}>
                <div className="text-xl">{tech.emoji}</div>
                <div className="text-xs font-semibold mt-1">{tech.name}</div>
              </div>
            ))}
          </div>
        </div>

        {/* References */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-4">📚 {t('about.references')}</h2>
          <ol className="space-y-2">
            {refs.map((ref, i) => (
              <li key={i} className="text-xs text-gray-600 leading-relaxed pl-2 border-l-2 border-blue-200">{ref}</li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}
