'use client';

import Link from 'next/link';

import { useI18n } from '@/lib/i18n';
import LanguageSwitcher from './LanguageSwitcher';

export default function Navbar() {
  const { t } = useI18n();

  return (
    <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-blue-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <span className="text-2xl">💧</span>
            <span className="font-bold text-primary-700 text-base sm:text-lg">
              HYDRO RAIN GUARD
            </span>
          </Link>

          <div className="flex items-center gap-1 sm:gap-4">
            <Link
              href="/"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors px-1.5"
            >
              {t('nav.home')}
            </Link>
            <Link
              href="/assess"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors px-1.5"
            >
              {t('nav.assess')}
            </Link>
            <Link
              href="/about"
              className="text-sm font-medium text-gray-600 hover:text-primary-700 transition-colors px-1.5"
            >
              {t('nav.about')}
            </Link>

            <LanguageSwitcher />

            <Link
              href="/assess"
              className="hidden sm:inline-block bg-primary-700 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-800 transition-colors whitespace-nowrap"
            >
              {t('nav.start')} →
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
