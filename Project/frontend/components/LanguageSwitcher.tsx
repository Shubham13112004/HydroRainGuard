'use client';

import { useEffect, useRef, useState } from 'react';
import { Globe, Check } from 'lucide-react';

import { LOCALES, LOCALE_META, useI18n, type Locale } from '@/lib/i18n';

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;

    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };

    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={t('lang.label')}
        aria-expanded={open}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium text-gray-600 hover:text-primary-700 hover:bg-blue-50 transition-colors"
      >
        <Globe className="w-4 h-4" />
        <span className="hidden sm:inline">
          {LOCALE_META[locale].native}
        </span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-44 bg-white rounded-xl shadow-lg border border-gray-100 py-1.5 z-[1000]">
          <p className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-400">
            {t('lang.label')}
          </p>
          {LOCALES.map((code: Locale) => (
            <button
              key={code}
              type="button"
              onClick={() => {
                setLocale(code);
                setOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 text-sm transition-colors ${
                code === locale
                  ? 'text-primary-700 bg-blue-50 font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="flex items-center gap-2">
                <span>{LOCALE_META[code].flag}</span>
                <span>{LOCALE_META[code].native}</span>
              </span>
              {code === locale && <Check className="w-4 h-4" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
