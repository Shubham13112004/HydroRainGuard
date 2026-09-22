'use client';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Droplets, Map, Brain, Camera, FileText, Cloud, ChevronRight, BarChart2, Waves, Leaf } from 'lucide-react';

const features = [
  { icon: Map, title: 'GIS & Remote Sensing', desc: 'Location-aware analysis using real coordinates to assess site-specific hydrological potential.', color: 'bg-blue-50 text-blue-700' },
  { icon: BarChart2, title: 'Hydrological Modelling', desc: 'Rational Method & SCS-CN based runoff estimation with monthly distribution across 12 months.', color: 'bg-green-50 text-green-700' },
  { icon: Brain, title: 'AI Recommendations', desc: 'Intelligent multi-criteria scoring engine recommends the most suitable recharge structures for your site.', color: 'bg-purple-50 text-purple-700' },
  { icon: Camera, title: 'AR Visualization', desc: 'Augmented Reality overlay shows recommended structures in 3D before any physical installation.', color: 'bg-orange-50 text-orange-700' },
  { icon: FileText, title: 'PDF Report Generation', desc: 'Auto-generates professional assessment reports with all calculations, charts, and recommendations.', color: 'bg-red-50 text-red-700' },
  { icon: Cloud, title: 'Real-time Weather', desc: 'Fetches live rainfall data from OpenWeatherMap API with regional IMD dataset fallback for India.', color: 'bg-cyan-50 text-cyan-700' },
];

const steps = [
  { num: '01', title: 'Data Input', desc: 'Basic info, roof details & site conditions', icon: '📋' },
  { num: '02', title: 'Weather Fetch', desc: 'Real-time rainfall from OpenWeatherMap', icon: '🌧️' },
  { num: '03', title: 'Hydro Analysis', desc: 'Runoff & recharge calculations', icon: '📊' },
  { num: '04', title: 'Feasibility Check', desc: 'AI-powered structure recommendations', icon: '🧠' },
  { num: '05', title: 'Report & AR', desc: 'PDF report & AR visualization', icon: '📄' },
];

const stats = [
  { value: '1.2B+', label: 'People facing water stress', icon: '💧' },
  { value: '40%', label: 'Urban runoff wasted', icon: '🏙️' },
  { value: '80%', label: 'Cities over-extracting groundwater', icon: '⛏️' },
  { value: '5-7yr', label: 'Typical payback period', icon: '💰' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden gradient-water text-white py-24 px-4">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="text-8xl mb-6 animate-float">💧</div>
            <h1 className="text-5xl md:text-6xl font-extrabold mb-4 leading-tight">
              HYDRO RAIN GUARD
            </h1>
            <p className="text-xl md:text-2xl font-light mb-2 text-blue-100">
              Intelligent Rainwater Harvesting & Artificial Recharge Assessment
            </p>
            <p className="text-base text-blue-200 mb-8 max-w-2xl mx-auto">
              An integrated GIS + AI + AR decision-support framework for sustainable groundwater management. 
              Assess your rooftop, get recharge structure recommendations, and download a professional report.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/assess"
                className="bg-white text-primary-700 font-bold px-8 py-4 rounded-xl hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl flex items-center gap-2 justify-center"
              >
                Start Assessment <ChevronRight className="w-5 h-5" />
              </Link>
              <Link
                href="/about"
                className="border-2 border-white text-white font-semibold px-8 py-4 rounded-xl hover:bg-white/10 transition-all flex items-center gap-2 justify-center"
              >
                Learn More <Leaf className="w-5 h-5" />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-white border-b border-gray-100 py-10">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl mb-1">{s.icon}</div>
              <div className="text-3xl font-extrabold text-primary-700">{s.value}</div>
              <div className="text-sm text-gray-500 mt-1">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-3">Framework Capabilities</h2>
          <p className="text-gray-500 text-center mb-12 max-w-xl mx-auto">Six integrated modules working together for comprehensive water resource assessment</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${f.color}`}>
                  <f.icon className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-gray-800 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-3">System Workflow</h2>
          <p className="text-gray-500 text-center mb-12">From data input to actionable recommendations in minutes</p>
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {steps.map((s, i) => (
              <div key={i} className="flex md:flex-col items-center gap-3 md:gap-2 flex-1">
                <div className="relative">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center text-2xl shadow-lg">
                    {s.icon}
                  </div>
                  <span className="absolute -top-2 -right-2 w-6 h-6 bg-secondary-500 text-white text-xs font-bold rounded-full flex items-center justify-center">{s.num}</span>
                </div>
                <div className="text-center">
                  <p className="font-bold text-gray-800 text-sm">{s.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 max-w-[100px]">{s.desc}</p>
                </div>
                {i < steps.length - 1 && (
                  <div className="hidden md:block text-primary-300 text-2xl font-light">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="gradient-water py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <Waves className="w-12 h-12 text-white/60 mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Assess Your Site?</h2>
          <p className="text-blue-100 mb-8">Get your complete hydrological assessment with recharge recommendations and PDF report in under 2 minutes.</p>
          <Link
            href="/assess"
            className="bg-white text-primary-700 font-bold px-10 py-4 rounded-xl hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl inline-flex items-center gap-2 text-lg"
          >
            Start Free Assessment <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
