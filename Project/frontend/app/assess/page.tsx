'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { useForm, type FieldError, type UseFormRegisterReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  MapPin,
  Droplets,
  Cloud,
  CheckCircle,
} from 'lucide-react';

import { submitAssessment, getWeatherPreview } from '@/lib/api';
import type { WeatherData } from '@/lib/types';
import { useI18n, type TranslationKey } from '@/lib/i18n';

/* Leaflet needs `window`, so the map is client-only. */
const MapPicker = dynamic(() => import('@/components/MapPicker'), {
  ssr: false,
  loading: () => (
    <div className="h-[280px] rounded-xl border border-gray-200 bg-blue-50/50 flex items-center justify-center">
      <Loader2 className="w-5 h-5 animate-spin text-primary-700" />
    </div>
  ),
});


/* ============================================================
   VALIDATION SCHEMA
============================================================ */

const schema = z.object({
  name: z.string().min(2),
  location: z.string().min(2),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
  num_people: z.coerce.number().int().min(1).max(500),
  roof_type: z.enum(['RCC', 'METAL', 'TILE', 'GREEN', 'ASPHALT']),
  roof_area: z.coerce.number().min(5).max(10000),
  open_space_area: z.coerce.number().min(0),
  soil_type: z.enum(['SANDY', 'LOAMY', 'CLAY', 'GRAVELLY', 'SILTY']),
  groundwater_depth: z.coerce.number().min(1).max(200),
  water_tariff_per_kl: z.coerce.number().min(0).max(1000),
  annual_rainfall_override: z
    .union([z.coerce.number().min(0).max(20000), z.literal('')])
    .optional(),
});

type FormData = z.infer<typeof schema>;


/* ============================================================
   FIELD COMPONENTS

   These live at MODULE scope on purpose. Declaring them inside
   AssessPage gave React a brand-new component type on every
   render, so every input was unmounted and recreated as you
   typed — the Latitude/Longitude fields lost focus after each
   keystroke. See ANALYSIS.md §4.3.
============================================================ */

type InputFieldProps = {
  label: string;
  error?: FieldError;
  register: UseFormRegisterReturn;
  type?: string;
  placeholder?: string;
  min?: string | number;
  max?: string | number;
  step?: string;
  hint?: string;
  suffix?: string;
};

function InputField({
  label,
  error,
  register,
  type = 'number',
  placeholder,
  min,
  max,
  step,
  hint,
  suffix,
}: InputFieldProps) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-1.5">
        {label}
      </label>

      <div className="relative">
        <input
          type={type}
          step={step}
          min={min}
          max={max}
          placeholder={placeholder}
          {...register}
          className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-gray-800 transition-all ${
            error ? 'border-red-300' : 'border-gray-200'
          } ${suffix ? 'pr-16' : ''}`}
        />
        {suffix && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-gray-400">
            {suffix}
          </span>
        )}
      </div>

      {error ? (
        <p className="text-red-500 text-xs mt-1">{String(error.message)}</p>
      ) : hint ? (
        <p className="text-gray-400 text-xs mt-1 leading-relaxed">{hint}</p>
      ) : null}
    </div>
  );
}

type SelectFieldProps = {
  label: string;
  error?: FieldError;
  register: UseFormRegisterReturn;
  options: Record<string, string>;
};

function SelectField({ label, error, register, options }: SelectFieldProps) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-1.5">
        {label}
      </label>

      <select
        {...register}
        className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-800 transition-all ${
          error ? 'border-red-300' : 'border-gray-200'
        }`}
      >
        {Object.entries(options).map(([value, labelText]) => (
          <option key={value} value={value}>
            {labelText}
          </option>
        ))}
      </select>

      {error && (
        <p className="text-red-500 text-xs mt-1">{String(error.message)}</p>
      )}
    </div>
  );
}


/* ============================================================
   STEP INFORMATION
============================================================ */

const stepMeta: { icon: string; titleKey: TranslationKey; descKey: TranslationKey }[] = [
  {
    icon: '👤',
    titleKey: 'assess.step1.title',
    descKey: 'assess.step1.desc',
  },
  {
    icon: '🏠',
    titleKey: 'assess.step2.title',
    descKey: 'assess.step2.desc',
  },
  {
    icon: '🌍',
    titleKey: 'assess.step3.title',
    descKey: 'assess.step3.desc',
  },
];

const stepFields: (keyof FormData)[][] = [
  ['name', 'location', 'latitude', 'longitude', 'num_people'],
  ['roof_type', 'roof_area'],
  ['open_space_area', 'soil_type', 'groundwater_depth', 'water_tariff_per_kl'],
];


/* ============================================================
   MAIN COMPONENT
============================================================ */

const DEFAULT_COORDS = { lat: 18.5204, lon: 73.8567 };

export default function AssessPage() {
  const router = useRouter();
  const { t, roofLabel, soilLabel } = useI18n();

  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  /* Local annual total the user types in to correct the coarse grid. */
  const [rainOverride, setRainOverride] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);

  /* Map pin position. Owned here so the map never needs a
     `watch()` subscription — which is what forced a re-render on
     every keystroke in the first place. */
  const [coords, setCoords] = useState(DEFAULT_COORDS);
  const [manualCoords, setManualCoords] = useState(false);
  const [locationTouched, setLocationTouched] = useState(false);

  const {
    register,
    trigger,
    getValues,
    setValue,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      latitude: DEFAULT_COORDS.lat,
      longitude: DEFAULT_COORDS.lon,
      location: 'Pune, Maharashtra',
      num_people: 4,
      roof_type: 'RCC',
      roof_area: 100,
      open_space_area: 50,
      soil_type: 'LOAMY',
      groundwater_depth: 15,
      water_tariff_per_kl: 35,
    },
  });

  /* ---------- map → form ---------- */

  const handleMapChange = (lat: number, lon: number, placeName?: string) => {
    setCoords({ lat, lon });
    setValue('latitude', lat, { shouldValidate: true });
    setValue('longitude', lon, { shouldValidate: true });

    // Auto-fill the location name until the user types their own.
    if (placeName && !locationTouched) {
      setValue('location', placeName, { shouldValidate: true });
    }
    setWeather(null);
  };

  /* ---------- navigation ---------- */

  const handleNext = async () => {
    setError(null);
    const valid = await trigger(stepFields[step]);
    if (!valid) return;
    if (step < 2) setStep(step + 1);
  };

  const handlePrevious = () => {
    setError(null);
    if (step > 0) setStep((c) => c - 1);
  };

  /* ---------- rainfall preview ---------- */

  const handleFetchWeather = async () => {
    setWeatherLoading(true);
    setError(null);
    try {
      // Read on demand instead of subscribing with watch().
      const { latitude, longitude, location } = getValues();
      const data = await getWeatherPreview(latitude, longitude, {
        annualRainfallOverride: rainOverride || null,
        locationName: location,
      });
      setWeather(data);
    } catch {
      setError(t('assess.error.weather'));
    } finally {
      setWeatherLoading(false);
    }
  };

  /* ---------- final submit ---------- */

  const onSubmit = async (data: FormData) => {
    if (step !== 2) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await submitAssessment({
        ...data,
        annual_rainfall_override: rainOverride || null,
        location_name: data.location,
      });
      localStorage.setItem('hydro_result', JSON.stringify(result));
      router.push(`/results?id=${result.assessment_id}`);
    } catch (e: any) {
      // A network failure has no `response` — say something useful.
      const detail =
        e?.response?.data?.detail ||
        (e?.code === 'ERR_NETWORK' || e?.message === 'Network Error'
          ? t('assess.error.backend')
          : null) ||
        t('assess.error.generic');

      setError(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunAssessment = () => {
    if (step !== 2) return;
    handleSubmit(onSubmit)();
  };

  const roofOptions = {
    RCC: roofLabel('RCC'),
    METAL: roofLabel('METAL'),
    TILE: roofLabel('TILE'),
    GREEN: roofLabel('GREEN'),
    ASPHALT: roofLabel('ASPHALT'),
  };

  const soilOptions = {
    SANDY: soilLabel('SANDY'),
    LOAMY: soilLabel('LOAMY'),
    CLAY: soilLabel('CLAY'),
    GRAVELLY: soilLabel('GRAVELLY'),
    SILTY: soilLabel('SILTY'),
  };

  /* ---------- render ---------- */

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* ---- step indicator ---- */}
        <div className="flex items-center justify-center mb-10">
          {stepMeta.map((item, index) => (
            <div key={index} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                    index < step
                      ? 'bg-secondary-500 text-white'
                      : index === step
                      ? 'bg-primary-700 text-white ring-4 ring-primary-200'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {index < step ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span
                  className={`text-xs mt-1 font-medium hidden sm:block ${
                    index === step ? 'text-primary-700' : 'text-gray-400'
                  }`}
                >
                  {t(item.titleKey)}
                </span>
              </div>

              {index < stepMeta.length - 1 && (
                <div
                  className={`h-0.5 w-16 sm:w-24 mx-2 transition-all ${
                    index < step ? 'bg-secondary-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* ---- card ---- */}
        <div className="bg-white rounded-3xl shadow-xl p-6 sm:p-8">
          <div className="mb-6">
            <div className="text-3xl mb-2">{stepMeta[step].icon}</div>
            <h2 className="text-2xl font-bold text-gray-800">
              {t(stepMeta[step].titleKey)}
            </h2>
            <p className="text-gray-500 text-sm mt-1">
              {t(stepMeta[step].descKey)}
            </p>
          </div>

          {/* No <form> element: Next/Previous must never submit. */}
          <AnimatePresence mode="wait">
            {/* ================= STEP 1 ================= */}
            {step === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <InputField
                  label={t('assess.field.name')}
                  type="text"
                  placeholder={t('assess.field.name.placeholder')}
                  error={errors.name}
                  register={register('name')}
                />

                <InputField
                  label={t('assess.field.people')}
                  type="number"
                  min="1"
                  max="500"
                  placeholder="4"
                  error={errors.num_people}
                  register={register('num_people')}
                />

                {/* ---- map pin ---- */}
                <div className="border border-dashed border-primary-200 rounded-xl p-4">
                  <p className="font-semibold text-sm text-gray-800">
                    {t('assess.map.title')}
                  </p>
                  <p className="text-xs text-gray-400 mb-3">
                    {t('assess.map.hint')}
                  </p>

                  <MapPicker
                    latitude={coords.lat}
                    longitude={coords.lon}
                    onChange={handleMapChange}
                  />

                  <div className="mt-3 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => setManualCoords((v) => !v)}
                      className="text-xs font-semibold text-primary-700 hover:underline"
                    >
                      {manualCoords
                        ? t('assess.map.mapToggle')
                        : t('assess.map.manualToggle')}
                    </button>
                  </div>

                  {manualCoords && (
                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <InputField
                        label={t('assess.map.lat')}
                        type="number"
                        step="0.0001"
                        error={errors.latitude}
                        register={register('latitude', {
                          onChange: (e) => {
                            const v = parseFloat(e.target.value);
                            if (!Number.isNaN(v)) {
                              setCoords((c) => ({ ...c, lat: v }));
                              setWeather(null);
                            }
                          },
                        })}
                      />
                      <InputField
                        label={t('assess.map.lon')}
                        type="number"
                        step="0.0001"
                        error={errors.longitude}
                        register={register('longitude', {
                          onChange: (e) => {
                            const v = parseFloat(e.target.value);
                            if (!Number.isNaN(v)) {
                              setCoords((c) => ({ ...c, lon: v }));
                              setWeather(null);
                            }
                          },
                        })}
                      />
                    </div>
                  )}
                </div>

                <InputField
                  label={t('assess.field.location')}
                  type="text"
                  placeholder={t('assess.field.location.placeholder')}
                  error={errors.location}
                  register={register('location', {
                    onChange: () => setLocationTouched(true),
                  })}
                />

                <div className="bg-blue-50 rounded-xl p-3 flex items-start gap-2">
                  <MapPin className="w-4 h-4 text-primary-600 mt-0.5 shrink-0" />
                  <p className="text-xs text-blue-700">
                    {t('assess.map.defaultNote')}
                  </p>
                </div>
              </motion.div>
            )}

            {/* ================= STEP 2 ================= */}
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <SelectField
                  label={t('assess.field.roofType')}
                  options={roofOptions}
                  error={errors.roof_type}
                  register={register('roof_type')}
                />

                <InputField
                  label={t('assess.field.roofArea')}
                  type="number"
                  min="5"
                  max="10000"
                  step="0.1"
                  placeholder="100"
                  suffix="m²"
                  error={errors.roof_area}
                  register={register('roof_area')}
                />

                {/* ---- rainfall ---- */}
                <div className="border border-dashed border-primary-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2 gap-3">
                    <div>
                      <p className="font-semibold text-sm text-gray-700">
                        {t('assess.weather.title')}
                      </p>
                      <p className="text-xs text-gray-400">
                        {t('assess.weather.subtitle')}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleFetchWeather}
                      disabled={weatherLoading}
                      className="flex shrink-0 items-center gap-2 bg-primary-700 text-white text-sm px-4 py-2 rounded-lg hover:bg-primary-800 transition-colors disabled:opacity-50"
                    >
                      {weatherLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Cloud className="w-4 h-4" />
                      )}
                      {t('assess.weather.fetch')}
                    </button>
                  </div>

                  {weather ? (
                    <>
                      <div className="grid grid-cols-2 gap-3 mt-3">
                        <MiniStat
                          label={t('assess.weather.location')}
                          value={weather.location_name}
                          tone="blue"
                        />
                        <MiniStat
                          label={t('assess.weather.rainfall')}
                          value={`${weather.annual_rainfall} ${t('common.mm')}`}
                          tone="green"
                        />
                        <MiniStat
                          label={t('assess.weather.temp')}
                          value={`${weather.avg_temperature}°C`}
                          tone="orange"
                        />
                        <MiniStat
                          label={t('assess.weather.humidity')}
                          value={`${weather.humidity}%`}
                          tone="cyan"
                        />
                      </div>

                      {/* ---- where the numbers come from ---- */}
                      <div className="mt-3 rounded-lg bg-gray-50 border border-gray-200 p-3 text-xs text-gray-500 space-y-1">
                        <p>
                          <span className="font-semibold text-gray-600">
                            {t('assess.rain.source')}:{' '}
                          </span>
                          {weather.rainfall_source}
                        </p>
                        <p>
                          <span className="font-semibold text-gray-600">
                            {t('assess.rain.period')}:{' '}
                          </span>
                          {weather.climatology_period}
                        </p>
                        <p>
                          <span className="font-semibold text-gray-600">
                            {t('assess.rain.cell')}:{' '}
                          </span>
                          {weather.grid_cell} ·{' '}
                          {weather.grid_resolution_deg}°
                        </p>
                      </div>

                      {weather.rainfall_is_grid_estimate && (
                        <div className="mt-2 rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
                          {t('assess.rain.gridWarning')}
                        </div>
                      )}

                      {/* ---- local override ---- */}
                      <div className="mt-3">
                        <label className="block text-xs font-semibold text-gray-600 mb-1">
                          {t('assess.rain.override')}
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="number"
                            min={0}
                            step={1}
                            value={rainOverride}
                            onChange={(e) =>
                              setRainOverride(
                                e.target.value === ''
                                  ? ''
                                  : Number(e.target.value),
                              )
                            }
                            placeholder={String(weather.annual_rainfall)}
                            className="w-32 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                          />
                          <button
                            type="button"
                            onClick={handleFetchWeather}
                            disabled={weatherLoading}
                            className="px-3 py-2 rounded-lg border border-primary-700 text-primary-700 text-xs font-semibold hover:bg-primary-50 disabled:opacity-50"
                          >
                            {t('assess.rain.apply')}
                          </button>
                          {rainOverride !== '' && (
                            <button
                              type="button"
                              onClick={() => {
                                setRainOverride('');
                                setWeather(null);
                                requestAnimationFrame(
                                  () => void handleFetchWeather(),
                                );
                              }}
                              className="px-3 py-2 rounded-lg border border-gray-300 text-gray-600 text-xs hover:bg-gray-50"
                            >
                              {t('assess.rain.clear')}
                            </button>
                          )}
                        </div>
                        <p className="mt-1 text-[11px] text-gray-400">
                          {t('assess.rain.overrideHint')}
                        </p>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-4 text-gray-400">
                      <Droplets className="w-8 h-8 mx-auto mb-1 opacity-40" />
                      <p className="text-xs">{t('assess.weather.empty')}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* ================= STEP 3 ================= */}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <InputField
                  label={t('assess.field.openSpace')}
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="50"
                  suffix="m²"
                  error={errors.open_space_area}
                  register={register('open_space_area')}
                />

                <SelectField
                  label={t('assess.field.soil')}
                  options={soilOptions}
                  error={errors.soil_type}
                  register={register('soil_type')}
                />

                <InputField
                  label={t('assess.field.depth')}
                  type="number"
                  min="1"
                  max="200"
                  step="0.5"
                  placeholder="15"
                  suffix="m"
                  error={errors.groundwater_depth}
                  register={register('groundwater_depth')}
                />

                <div className="bg-green-50 rounded-xl p-3">
                  <p className="text-xs text-green-700">
                    💡 <strong>Tip:</strong> {t('assess.tip.depth')}
                  </p>
                </div>

                <InputField
                  label={t('assess.field.tariff')}
                  type="number"
                  min="0"
                  step="1"
                  placeholder="35"
                  suffix="₹/KL"
                  hint={t('assess.field.tariff.hint')}
                  error={errors.water_tariff_per_kl}
                  register={register('water_tariff_per_kl')}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* ---- error ---- */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* ---- navigation ---- */}
          <div className="flex justify-between mt-8">
            <button
              type="button"
              onClick={handlePrevious}
              disabled={step === 0 || isLoading}
              className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              {t('assess.button.previous')}
            </button>

            {step < 2 ? (
              <button
                type="button"
                onClick={handleNext}
                disabled={isLoading}
                className="flex items-center gap-2 bg-primary-700 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-800 transition-all disabled:opacity-50"
              >
                {t('assess.button.next')}
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleRunAssessment}
                disabled={isLoading}
                className="flex items-center gap-2 bg-secondary-500 text-white px-7 py-3 rounded-xl font-bold hover:bg-secondary-600 transition-all disabled:opacity-70"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    {t('assess.button.running')}
                  </>
                ) : (
                  <>{t('assess.button.run')} 🚀</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const TONES: Record<string, string> = {
  blue: 'bg-blue-50 text-primary-700',
  green: 'bg-green-50 text-green-700',
  orange: 'bg-orange-50 text-orange-700',
  cyan: 'bg-cyan-50 text-cyan-700',
};

function MiniStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: keyof typeof TONES;
}) {
  return (
    <div className={`rounded-lg p-3 ${TONES[tone]}`}>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="font-bold text-sm truncate">{value}</p>
    </div>
  );
}
