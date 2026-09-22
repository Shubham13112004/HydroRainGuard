import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import Script from 'next/script';

export const metadata: Metadata = {
  title: 'HYDRO RAIN GUARD | Intelligent Rainwater Harvesting Assessment',
  description: 'An integrated framework for rooftop rainwater harvesting and artificial groundwater recharge assessment using GIS, AI, and AR.',
  keywords: 'rainwater harvesting, groundwater recharge, GIS, hydrological modelling, India',
};

function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-blue-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">💧</span>
            <span className="font-bold text-primary-700 text-lg">HYDRO RAIN GUARD</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link href="/" className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors">Home</Link>
            <Link href="/assess" className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors">Assess</Link>
            <Link href="/about" className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors">About</Link>
            <Link href="/assess" className="bg-primary-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-800 transition-colors">
              Start Assessment →
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 py-8 mt-16">
      <div className="max-w-7xl mx-auto px-4 text-center">
        <p className="font-semibold text-white mb-1">💧 HYDRO RAIN GUARD</p>
        <p className="text-sm">ICICIS Conference 2026 | JSPM's Rajarshi Shahu College of Engineering, Pune</p>
        <p className="text-xs mt-2">Authors: Dr. Dipali Patil • Shubham Desai • Siddhesh Mahadik • Kaushal Agale • Omkar Kshirsagar</p>
        <p className="text-xs mt-1">Paper ID: 195 | An Integrated Conceptual Framework for Intelligent Rainwater Harvesting & Artificial Recharge Assessment</p>
      </div>
    </footer>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script src="https://aframe.io/releases/1.5.0/aframe.min.js" strategy="beforeInteractive" />
      </head>
      <body className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="pt-16">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
