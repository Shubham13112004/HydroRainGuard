import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

import { LanguageProvider } from '@/lib/i18n';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'HYDRO RAIN GUARD | Intelligent Rainwater Harvesting Assessment',
  description:
    'An integrated framework for rooftop rainwater harvesting and artificial groundwater recharge assessment using GIS, rainfall modelling and 3D/AR visualisation.',
  keywords:
    'rainwater harvesting, groundwater recharge, hydrological modelling, India, मराठी, हिन्दी',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/*
          A-Frame is no longer loaded here. It used to be pulled in with
          `beforeInteractive` on EVERY route (~1 MB) even though only the
          AR page needed it. The 3D view is now react-three-fiber, loaded
          lazily on /ar only.
        */}
      </head>
      <body className="min-h-screen bg-gray-50">
        <LanguageProvider>
          <Navbar />
          <main className="pt-16">{children}</main>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  );
}
