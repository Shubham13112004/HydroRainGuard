'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { en, type TranslationKey } from './en';
import { hi } from './hi';
import { mr } from './mr';

/* ============================================================
   LOCALES
============================================================ */

export const LOCALES = ['en', 'hi', 'mr'] as const;
export type Locale = (typeof LOCALES)[number];

export const LOCALE_META: Record<
  Locale,
  { label: string; native: string; flag: string; htmlLang: string }
> = {
  en: {
    label: 'English',
    native: 'English',
    flag: '🇬🇧',
    htmlLang: 'en',
  },
  hi: {
    label: 'Hindi',
    native: 'हिन्दी',
    flag: '🇮🇳',
    htmlLang: 'hi',
  },
  mr: {
    label: 'Marathi',
    native: 'मराठी',
    flag: '🇮🇳',
    htmlLang: 'mr',
  },
};

const DICTIONARIES: Record<
  Locale,
  Partial<Record<TranslationKey, string>>
> = {
  en,
  hi,
  mr,
};

const STORAGE_KEY = 'hydro_locale';

/* ============================================================
   ENUM LABELS
   Backend returns stable English enum values; these are the
   human labels, translated per locale.
============================================================ */

export const ROOF_LABELS: Record<Locale, Record<string, string>> = {
  en: {
    RCC: 'RCC Concrete',
    METAL: 'Metal / GI Sheet',
    TILE: 'Clay / Mangalore Tile',
    GREEN: 'Green Roof',
    ASPHALT: 'Asphalt / Bitumen',
  },
  hi: {
    RCC: 'आरसीसी कंक्रीट',
    METAL: 'धातु / जीआई शीट',
    TILE: 'मिट्टी / मैंगलोर टाइल',
    GREEN: 'हरी छत',
    ASPHALT: 'डामर / बिटुमेन',
  },
  mr: {
    RCC: 'आरसीसी कॉंक्रिट',
    METAL: 'धातू / जीआय पत्रा',
    TILE: 'माती / मंगळूर कौल',
    GREEN: 'हिरवी छत',
    ASPHALT: 'डांबर / बिट्यूमेन',
  },
};

export const SOIL_LABELS: Record<Locale, Record<string, string>> = {
  en: {
    SANDY: 'Sandy (high permeability)',
    LOAMY: 'Loamy (moderate permeability)',
    CLAY: 'Clay (low permeability)',
    GRAVELLY: 'Gravelly (very high permeability)',
    SILTY: 'Silty (moderate-low permeability)',
  },
  hi: {
    SANDY: 'रेतीली (उच्च पारगम्यता)',
    LOAMY: 'दोमट (मध्यम पारगम्यता)',
    CLAY: 'चिकनी मिट्टी (कम पारगम्यता)',
    GRAVELLY: 'कंकड़ीली (अत्यधिक पारगम्यता)',
    SILTY: 'गादयुक्त (मध्यम-कम पारगम्यता)',
  },
  mr: {
    SANDY: 'वाळूमय (उच्च पारगम्यता)',
    LOAMY: 'चिकणमाती मिश्र (मध्यम पारगम्यता)',
    CLAY: 'चिकणमाती (कमी पारगम्यता)',
    GRAVELLY: 'खडीमय (अत्यंत उच्च पारगम्यता)',
    SILTY: 'गाळयुक्त (मध्यम-कमी पारगम्यता)',
  },
};

/**
 * Structure names come back from the backend in English.
 * These are display-only translations; the API contract and
 * the PDF report stay in English.
 */
export const STRUCTURE_LABELS: Record<Locale, Record<string, string>> = {
  en: {
    'Rooftop Storage Tank': 'Rooftop Storage Tank',
    'Recharge Pit': 'Recharge Pit',
    'Recharge Well / Borewell Recharge': 'Recharge Well',
    'Percolation Tank': 'Percolation Tank',
    'Soak Pit / French Drain': 'Soak Pit / French Drain',
  },
  hi: {
    'Rooftop Storage Tank': 'छत भंडारण टैंक',
    'Recharge Pit': 'पुनर्भरण गड्ढा',
    'Recharge Well / Borewell Recharge': 'पुनर्भरण कुआँ',
    'Percolation Tank': 'रिसाव टैंक',
    'Soak Pit / French Drain': 'सोक पिट',
  },
  mr: {
    'Rooftop Storage Tank': 'छतावरील साठवण टाकी',
    'Recharge Pit': 'पुनर्भरण खड्डा',
    'Recharge Well / Borewell Recharge': 'पुनर्भरण विहीर',
    'Percolation Tank': 'मुरण तलाव',
    'Soak Pit / French Drain': 'मुर खड्डा',
  },
};

/* ============================================================
   CONTEXT
============================================================ */

type I18nValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: TranslationKey) => string;
  roofLabel: (v: string) => string;
  soilLabel: (v: string) => string;
  structureLabel: (v: string) => string;
};

const I18nContext = createContext<I18nValue | null>(null);

function readStoredLocale(): Locale {
  if (typeof window === 'undefined') return 'en';
  const saved = window.localStorage.getItem(STORAGE_KEY);
  return LOCALES.includes(saved as Locale) ? (saved as Locale) : 'en';
}

export function LanguageProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [locale, setLocaleState] = useState<Locale>('en');

  // Read after mount so server and client markup match.
  useEffect(() => {
    setLocaleState(readStoredLocale());
  }, []);

  // Keep <html lang> in sync for screen readers and fonts.
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = LOCALE_META[locale].htmlLang;
      document.documentElement.dataset.locale = locale;
    }
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* private mode — the choice just won't persist */
    }
  }, []);

  const t = useCallback(
    (key: TranslationKey) =>
      DICTIONARIES[locale][key] ?? en[key] ?? key,
    [locale],
  );

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      setLocale,
      t,
      roofLabel: (v) => ROOF_LABELS[locale][v] ?? v,
      soilLabel: (v) => SOIL_LABELS[locale][v] ?? v,
      structureLabel: (v) => STRUCTURE_LABELS[locale][v] ?? v,
    }),
    [locale, setLocale, t],
  );

  return (
    <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
  );
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used inside <LanguageProvider>');
  }
  return ctx;
}

export type { TranslationKey };
