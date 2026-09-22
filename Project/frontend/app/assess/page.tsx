'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
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

import {
  submitAssessment,
  getWeatherPreview,
} from '@/lib/api';

import type { WeatherData } from '@/lib/types';

import {
  ROOF_TYPE_LABELS,
  SOIL_TYPE_LABELS,
} from '@/lib/utils';


/* ============================================================
   VALIDATION SCHEMA
============================================================ */

const schema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters'),

  location: z
    .string()
    .min(2, 'Location name required'),

  latitude: z
    .coerce
    .number()
    .min(-90)
    .max(90),

  longitude: z
    .coerce
    .number()
    .min(-180)
    .max(180),

  num_people: z
    .coerce
    .number()
    .int()
    .min(1)
    .max(500),

  roof_type: z.enum([
    'RCC',
    'METAL',
    'TILE',
    'GREEN',
    'ASPHALT',
  ]),

  roof_area: z
    .coerce
    .number()
    .min(5, 'Minimum 5 m²')
    .max(10000),

  open_space_area: z
    .coerce
    .number()
    .min(0),

  soil_type: z.enum([
    'SANDY',
    'LOAMY',
    'CLAY',
    'GRAVELLY',
    'SILTY',
  ]),

  groundwater_depth: z
    .coerce
    .number()
    .min(1)
    .max(200),
});


type FormData = z.infer<typeof schema>;


/* ============================================================
   STEP INFORMATION
============================================================ */

const stepTitles = [
  {
    title: 'Basic Information',
    icon: '👤',
    desc: 'Tell us about the project and location',
  },
  {
    title: 'Roof Details',
    icon: '🏠',
    desc: 'Rooftop specifications and rainfall data',
  },
  {
    title: 'Site Condition',
    icon: '🌍',
    desc: 'Soil and groundwater characteristics',
  },
];


/* ============================================================
   MAIN COMPONENT
============================================================ */

export default function AssessPage() {

  const router = useRouter();

  const [step, setStep] = useState(0);

  const [isLoading, setIsLoading] = useState(false);

  const [weather, setWeather] =
    useState<WeatherData | null>(null);

  const [weatherLoading, setWeatherLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);


  /* ==========================================================
     FORM
  ========================================================== */

  const {
    register,
    trigger,
    watch,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),

    defaultValues: {
      latitude: 18.5204,
      longitude: 73.8567,

      location: 'Pune, Maharashtra',

      num_people: 4,

      roof_type: 'RCC',

      roof_area: 100,

      open_space_area: 50,

      soil_type: 'LOAMY',

      groundwater_depth: 15,
    },
  });


  /* ==========================================================
     WATCH COORDINATES
  ========================================================== */

  const lat = watch('latitude');
  const lon = watch('longitude');


  /* ==========================================================
     FIELDS FOR EACH STEP
  ========================================================== */

  const stepFields: (keyof FormData)[][] = [

    // STEP 1
    [
      'name',
      'location',
      'latitude',
      'longitude',
      'num_people',
    ],

    // STEP 2
    [
      'roof_type',
      'roof_area',
    ],

    // STEP 3
    [
      'open_space_area',
      'soil_type',
      'groundwater_depth',
    ],
  ];


  /* ==========================================================
     NEXT BUTTON
     
     IMPORTANT:
     This function ONLY changes the step.
     It NEVER submits the assessment.
  ========================================================== */

  const handleNext = async () => {

    // Clear old error
    setError(null);

    // Validate ONLY the current step
    const valid = await trigger(stepFields[step]);

    if (!valid) {
      return;
    }

    // STEP 1 → STEP 2
    if (step === 0) {
      setStep(1);
      return;
    }

    // STEP 2 → STEP 3
    if (step === 1) {
      setStep(2);
      return;
    }
  };


  /* ==========================================================
     PREVIOUS BUTTON
  ========================================================== */

  const handlePrevious = () => {

    setError(null);

    if (step > 0) {
      setStep((current) => current - 1);
    }
  };


  /* ==========================================================
     WEATHER
  ========================================================== */

  const handleFetchWeather = async () => {

    setWeatherLoading(true);

    setError(null);

    try {

      const data = await getWeatherPreview(
        lat,
        lon
      );

      setWeather(data);

    } catch (err) {

      console.error('Weather error:', err);

      setError(
        'Failed to fetch weather. Using regional estimates.'
      );

    } finally {

      setWeatherLoading(false);
    }
  };


  /* ==========================================================
     FINAL ASSESSMENT
     
     THIS IS THE ONLY FUNCTION THAT CALLS THE BACKEND.
  ========================================================== */

  const onSubmit = async (data: FormData) => {

    // Safety guard
    // Even if something accidentally calls this function,
    // do NOT submit unless we are on Step 3.

    if (step !== 2) {
      console.warn(
        'Assessment submission blocked: user is not on Step 3.'
      );

      return;
    }

    setIsLoading(true);

    setError(null);

    try {

      console.log(
        'Submitting final assessment:',
        data
      );

      const result = await submitAssessment(data);

      console.log(
        'Assessment successful:',
        result
      );

      localStorage.setItem(
        'hydro_result',
        JSON.stringify(result)
      );

      router.push(
        `/results?id=${result.assessment_id}`
      );

    } catch (e: any) {

      console.error(
        'Assessment submission error:',
        e
      );

      setError(
        e?.response?.data?.detail ||
        e?.message ||
        'Assessment failed. Please try again.'
      );

    } finally {

      setIsLoading(false);
    }
  };


  /* ============================================================
     FINAL BUTTON HANDLER
     
     Instead of using <button type="submit">,
     explicitly execute react-hook-form validation.
  ============================================================ */

  const handleRunAssessment = () => {

    if (step !== 2) {
      return;
    }

    handleSubmit(onSubmit)();
  };


  /* ============================================================
     INPUT COMPONENT
  ============================================================ */

  const InputField = ({
    label,
    name,
    type = 'number',
    placeholder,
    min,
    max,
    step: stepVal,
  }: any) => (

    <div>

      <label className="block text-sm font-semibold text-gray-700 mb-1.5">
        {label}
      </label>

      <input
        type={type}
        step={stepVal}
        min={min}
        max={max}
        placeholder={placeholder}
        {...register(name)}
        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-gray-800 transition-all"
      />

      {errors[name as keyof FormData] && (

        <p className="text-red-500 text-xs mt-1">

          {errors[name as keyof FormData]?.message as string}

        </p>

      )}

    </div>
  );


  /* ============================================================
     SELECT COMPONENT
  ============================================================ */

  const SelectField = ({
    label,
    name,
    options,
  }: {
    label: string;
    name: keyof FormData;
    options: Record<string, string>;
  }) => (

    <div>

      <label className="block text-sm font-semibold text-gray-700 mb-1.5">
        {label}
      </label>

      <select
        {...register(name)}
        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-800 transition-all"
      >

        {Object.entries(options).map(
          ([value, labelText]) => (

            <option
              key={value}
              value={value}
            >
              {labelText}
            </option>

          )
        )}

      </select>

      {errors[name] && (

        <p className="text-red-500 text-xs mt-1">

          {errors[name]?.message as string}

        </p>

      )}

    </div>
  );


  /* ============================================================
     UI
  ============================================================ */

  return (

    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-12 px-4">

      <div className="max-w-2xl mx-auto">


        {/* ======================================================
            STEP INDICATOR
        ====================================================== */}

        <div className="flex items-center justify-center mb-10">

          {stepTitles.map((item, index) => (

            <div
              key={index}
              className="flex items-center"
            >

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
                    index === step
                      ? 'text-primary-700'
                      : 'text-gray-400'
                  }`}
                >
                  {item.title}
                </span>

              </div>


              {index < stepTitles.length - 1 && (

                <div
                  className={`h-0.5 w-16 sm:w-24 mx-2 transition-all ${
                    index < step
                      ? 'bg-secondary-500'
                      : 'bg-gray-200'
                  }`}
                />

              )}

            </div>

          ))}

        </div>


        {/* ======================================================
            CARD
        ====================================================== */}

        <div className="bg-white rounded-3xl shadow-xl p-8">

          <div className="mb-6">

            <div className="text-3xl mb-2">
              {stepTitles[step].icon}
            </div>

            <h2 className="text-2xl font-bold text-gray-800">
              {stepTitles[step].title}
            </h2>

            <p className="text-gray-500 text-sm mt-1">
              {stepTitles[step].desc}
            </p>

          </div>


          {/* ====================================================
              IMPORTANT:
              NO <form onSubmit> around the wizard.
              
              This prevents Step 1/2 from ever submitting
              the final assessment.
          ==================================================== */}

          <AnimatePresence mode="wait">


            {/* ==================================================
                STEP 1
            ================================================== */}

            {step === 0 && (

              <motion.div
                key="step0"
                initial={{
                  opacity: 0,
                  x: 20,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                exit={{
                  opacity: 0,
                  x: -20,
                }}
                className="space-y-4"
              >

                <InputField
                  label="Full Name / Project Name"
                  name="name"
                  type="text"
                  placeholder="e.g. Rahul Sharma / Shivaji Nagar Society"
                />

                <InputField
                  label="Location Name"
                  name="location"
                  type="text"
                  placeholder="e.g. Pune, Maharashtra"
                />

                <div className="grid grid-cols-2 gap-4">

                  <InputField
                    label="Latitude"
                    name="latitude"
                    type="number"
                    stepVal="0.0001"
                    placeholder="18.5204"
                  />

                  <InputField
                    label="Longitude"
                    name="longitude"
                    type="number"
                    stepVal="0.0001"
                    placeholder="73.8567"
                  />

                </div>

                <div className="bg-blue-50 rounded-xl p-3 flex items-start gap-2">

                  <MapPin className="w-4 h-4 text-primary-600 mt-0.5 shrink-0" />

                  <p className="text-xs text-blue-700">
                    Default coordinates are set to Pune.
                    Use Google Maps to find your exact coordinates:
                    right-click on your location → "What's here?"
                  </p>

                </div>

                <InputField
                  label="Number of Occupants / People"
                  name="num_people"
                  type="number"
                  min="1"
                  max="500"
                  placeholder="4"
                />

              </motion.div>

            )}


            {/* ==================================================
                STEP 2
            ================================================== */}

            {step === 1 && (

              <motion.div
                key="step1"
                initial={{
                  opacity: 0,
                  x: 20,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                exit={{
                  opacity: 0,
                  x: -20,
                }}
                className="space-y-4"
              >

                <SelectField
                  label="Roof Type"
                  name="roof_type"
                  options={ROOF_TYPE_LABELS}
                />

                <InputField
                  label="Roof Area (m²)"
                  name="roof_area"
                  type="number"
                  min="5"
                  max="10000"
                  stepVal="0.1"
                  placeholder="100"
                />


                {/* WEATHER */}

                <div className="border border-dashed border-primary-200 rounded-xl p-4">

                  <div className="flex items-center justify-between mb-2">

                    <div>

                      <p className="font-semibold text-sm text-gray-700">
                        Rainfall Data Preview
                      </p>

                      <p className="text-xs text-gray-400">
                        Fetch weather data for your coordinates
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={handleFetchWeather}
                      disabled={weatherLoading}
                      className="flex items-center gap-2 bg-primary-700 text-white text-sm px-4 py-2 rounded-lg hover:bg-primary-800 transition-colors disabled:opacity-50"
                    >

                      {weatherLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Cloud className="w-4 h-4" />
                      )}

                      Fetch Weather

                    </button>

                  </div>


                  {weather ? (

                    <div className="grid grid-cols-2 gap-3 mt-3">

                      <div className="bg-blue-50 rounded-lg p-3">

                        <p className="text-xs text-gray-500">
                          Location
                        </p>

                        <p className="font-bold text-primary-700 text-sm">
                          {weather.location_name}
                        </p>

                      </div>


                      <div className="bg-green-50 rounded-lg p-3">

                        <p className="text-xs text-gray-500">
                          Annual Rainfall
                        </p>

                        <p className="font-bold text-green-700 text-sm">
                          {weather.annual_rainfall} mm
                        </p>

                      </div>


                      <div className="bg-orange-50 rounded-lg p-3">

                        <p className="text-xs text-gray-500">
                          Avg Temperature
                        </p>

                        <p className="font-bold text-orange-700 text-sm">
                          {weather.avg_temperature}°C
                        </p>

                      </div>


                      <div className="bg-cyan-50 rounded-lg p-3">

                        <p className="text-xs text-gray-500">
                          Humidity
                        </p>

                        <p className="font-bold text-cyan-700 text-sm">
                          {weather.humidity}%
                        </p>

                      </div>

                    </div>

                  ) : (

                    <div className="text-center py-4 text-gray-400">

                      <Droplets className="w-8 h-8 mx-auto mb-1 opacity-40" />

                      <p className="text-xs">
                        Click "Fetch Weather" to preview rainfall data
                      </p>

                    </div>

                  )}

                </div>

              </motion.div>

            )}


            {/* ==================================================
                STEP 3
            ================================================== */}

            {step === 2 && (

              <motion.div
                key="step2"
                initial={{
                  opacity: 0,
                  x: 20,
                }}
                animate={{
                  opacity: 1,
                  x: 0,
                }}
                exit={{
                  opacity: 0,
                  x: -20,
                }}
                className="space-y-4"
              >

                <InputField
                  label="Open Space / Garden Area (m²)"
                  name="open_space_area"
                  type="number"
                  min="0"
                  stepVal="0.1"
                  placeholder="50"
                />

                <SelectField
                  label="Soil Type"
                  name="soil_type"
                  options={SOIL_TYPE_LABELS}
                />

                <InputField
                  label="Groundwater / Borewell Depth (meters)"
                  name="groundwater_depth"
                  type="number"
                  min="1"
                  max="200"
                  stepVal="0.5"
                  placeholder="15"
                />

                <div className="bg-green-50 rounded-xl p-3">

                  <p className="text-xs text-green-700">

                    💡 <strong>Tip:</strong> You can check your local
                    groundwater depth from your building's borewell log,
                    or ask your local groundwater authority.

                    Typical values: Pune 10–25m, Mumbai 5–15m,
                    Delhi 15–40m.

                  </p>

                </div>

              </motion.div>

            )}

          </AnimatePresence>


          {/* ====================================================
              ERROR
          ==================================================== */}

          {error && (

            <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">

              ⚠️ {error}

            </div>

          )}


          {/* ====================================================
              NAVIGATION
          ==================================================== */}

          <div className="flex justify-between mt-8">


            {/* PREVIOUS */}

            <button
              type="button"
              onClick={handlePrevious}
              disabled={step === 0 || isLoading}
              className="flex items-center gap-2 px-6 py-3 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >

              <ChevronLeft className="w-4 h-4" />

              Previous

            </button>


            {/* ==================================================
                STEP 1 / STEP 2 NEXT
            ================================================== */}

            {step < 2 && (

              <button
                type="button"
                onClick={handleNext}
                disabled={isLoading}
                className="flex items-center gap-2 bg-primary-700 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-800 transition-all disabled:opacity-50"
              >

                Next

                <ChevronRight className="w-4 h-4" />

              </button>

            )}


            {/* ==================================================
                STEP 3 FINAL BUTTON
            ================================================== */}

            {step === 2 && (

              <button
                type="button"
                onClick={handleRunAssessment}
                disabled={isLoading}
                className="flex items-center gap-2 bg-secondary-500 text-white px-8 py-3 rounded-xl font-bold hover:bg-secondary-600 transition-all disabled:opacity-70"
              >

                {isLoading ? (

                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />

                    Analyzing...
                  </>

                ) : (

                  <>
                    Run Assessment 🚀
                  </>

                )}

              </button>

            )}

          </div>

        </div>

      </div>

    </div>
  );
}
