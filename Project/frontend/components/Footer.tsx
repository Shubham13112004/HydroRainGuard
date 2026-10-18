'use client';

import { useI18n } from '@/lib/i18n';

export default function Footer() {
  const { t } = useI18n();

  return (
    <footer className="bg-gray-900 text-gray-400 py-8 mt-16">
      <div className="max-w-7xl mx-auto px-4 text-center">
        <p className="font-semibold text-white mb-1">💧 HYDRO RAIN GUARD</p>
        <p className="text-sm">{t('footer.tagline')}</p>
        <p className="text-xs mt-2">
          {t('footer.authors')}: Dr. Dipali Patil • Shubham Desai • Siddhesh
          Mahadik • Kaushal Agale • Omkar Kshirsagar
        </p>
        <p className="text-xs mt-1">{t('footer.paper')}</p>
      </div>
    </footer>
  );
}
