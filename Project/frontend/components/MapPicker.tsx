'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  useMap,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { Search, Locate, Loader2 } from 'lucide-react';
import { useI18n } from '@/lib/i18n';

/* ============================================================
   MARKER ICON
   A pure HTML/SVG marker. Leaflet's default icon is broken by
   bundlers (its image URLs get rewritten), and a div-icon also
   avoids a network request just to draw a pin.
============================================================ */

const PIN_HTML = `
<div style="
  width:34px;height:34px;border-radius:50% 50% 50% 0;
  transform:rotate(-45deg);
  background:#0d70b0;
  border:3px solid #ffffff;
  box-shadow:0 3px 10px rgba(13,92,140,.45);
  display:flex;align-items:center;justify-content:center;">
  <span style="transform:rotate(45deg);font-size:14px;line-height:1;">💧</span>
</div>`;

const pinIcon = L.divIcon({
  className: 'hydro-map-pin',
  html: PIN_HTML,
  iconSize: [34, 34],
  iconAnchor: [17, 34],
});

/* ============================================================
   GEOCODING  (OpenStreetMap Nominatim — free, no API key)
   Reverse lookups only fire when the user releases the pin,
   never per-pixel, to respect the 1 req/s usage policy.
============================================================ */

type NominatimAddress = {
  city?: string;
  town?: string;
  village?: string;
  suburb?: string;
  county?: string;
  state_district?: string;
  state?: string;
  country?: string;
};

function readablePlace(a: NominatimAddress): string {
  return (
    a.city ||
    a.town ||
    a.village ||
    a.suburb ||
    a.county ||
    a.state_district ||
    a.state ||
    ''
  );
}

async function reverseGeocode(
  lat: number,
  lon: number,
): Promise<string> {
  const url =
    'https://nominatim.openstreetmap.org/reverse' +
    `?format=jsonv2&lat=${lat}&lon=${lon}&zoom=16&addressdetails=1`;

  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('reverse geocode failed');

  const data = await res.json();
  const place = readablePlace(data?.address ?? {});
  const display: string = data?.display_name ?? '';

  return place || display.split(',').slice(0, 2).join(',').trim();
}

async function forwardGeocode(q: string): Promise<{
  lat: number;
  lon: number;
  name: string;
} | null> {
  const url =
    'https://nominatim.openstreetmap.org/search' +
    `?format=jsonv2&q=${encodeURIComponent(q)}&limit=1&addressdetails=1`;

  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('geocode failed');

  const data = await res.json();
  if (!Array.isArray(data) || data.length === 0) return null;

  return {
    lat: parseFloat(data[0].lat),
    lon: parseFloat(data[0].lon),
    name: (data[0].display_name ?? '').split(',').slice(0, 2).join(',').trim(),
  };
}

/* ============================================================
   MAP HELPERS
============================================================ */

function Recenter({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lon], map.getZoom(), { animate: true });
  }, [lat, lon, map]);
  return null;
}

function ClickToPin({
  onPick,
}: {
  onPick: (lat: number, lon: number) => void;
}) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

/* ============================================================
   COMPONENT
============================================================ */

type Props = {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lon: number, placeName?: string) => void;
};

export default function MapPicker({
  latitude,
  longitude,
  onChange,
}: Props) {
  const { t } = useI18n();

  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [place, setPlace] = useState('');
  const [looking, setLooking] = useState(false);
  /* Tile loading is counted, not treated as boolean: a single 404
     tile (routine while panning or at the edge of coverage) must not
     blank the map. We only warn when nothing at all has loaded. */
  const [tiles, setTiles] = useState({ loaded: 0, failed: 0 });
  const tilesBlocked = tiles.failed >= 3 && tiles.loaded === 0;

  // Keep the latest onChange without re-creating map callbacks.
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  const handlePick = useCallback(
    async (lat: number, lon: number) => {
      const rounded = {
        lat: Math.round(lat * 1e4) / 1e4,
        lon: Math.round(lon * 1e4) / 1e4,
      };

      onChangeRef.current(rounded.lat, rounded.lon);

      try {
        const name = await reverseGeocode(rounded.lat, rounded.lon);
        setPlace(name);
        onChangeRef.current(rounded.lat, rounded.lon, name);
      } catch {
        // Geocoding is a nicety — coordinates still stand.
        setPlace('');
      }
    },
    [],
  );

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(false);
    try {
      const hit = await forwardGeocode(query.trim());
      if (hit) {
        setPlace(hit.name);
        onChangeRef.current(hit.lat, hit.lon, hit.name);
      } else {
        setSearchError(true);
      }
    } catch {
      setSearchError(true);
    } finally {
      setSearching(false);
    }
  };

  const handleLocate = () => {
    if (!navigator.geolocation) return;
    setLooking(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        setLooking(false);
        await handlePick(pos.coords.latitude, pos.coords.longitude);
      },
      () => setLooking(false),
      { timeout: 8000 },
    );
  };

  return (
    <div className="space-y-3">
      {/* ---- search row ---- */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
              }
            }}
            placeholder={t('assess.map.search')}
            className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white text-gray-800"
          />
        </div>

        <button
          type="button"
          onClick={handleSearch}
          disabled={searching || !query.trim()}
          className="px-4 py-2.5 rounded-xl bg-primary-700 text-white text-sm font-semibold hover:bg-primary-800 transition-colors disabled:opacity-50"
        >
          {searching ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            t('assess.map.search')
          )}
        </button>

        <button
          type="button"
          onClick={handleLocate}
          disabled={looking}
          title={t('assess.map.locate')}
          className="px-3 py-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          {looking ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Locate className="w-4 h-4" />
          )}
        </button>
      </div>

      {searchError && (
        <p className="text-xs text-amber-600">
          {t('assess.map.notFound')}
        </p>
      )}

      {/* ---- map ---- */}
      {/* Height is set inline as well as via h-[280px]: Leaflet
          measures its container on mount, and a container that is
          still 0px tall gives you a blank map. */}
      <div
        className="relative rounded-xl overflow-hidden border border-gray-200 h-[280px]"
        style={{ height: 280 }}
      >
        {tilesBlocked && (
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 z-[500] bg-amber-50/95 border-t border-amber-200 px-3 py-2 text-center">
            <p className="text-xs font-semibold text-amber-800">
              {t('assess.map.tilesFailed')}
            </p>
            <p className="text-[11px] text-amber-700">
              {t('assess.map.tilesFailedHint')}
            </p>
          </div>
        )}
        <MapContainer
          center={[latitude, longitude]}
          zoom={13}
          scrollWheelZoom
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
            eventHandlers={{
              load: () => setTiles((s) => ({ loaded: s.loaded + 1, failed: s.failed })),
              tileerror: () =>
                setTiles((s) => ({ loaded: s.loaded, failed: s.failed + 1 })),
            }}
          />
          <Recenter lat={latitude} lon={longitude} />
          <ClickToPin onPick={handlePick} />
          <Marker
            position={[latitude, longitude]}
            icon={pinIcon}
            draggable
            eventHandlers={{
              dragend: (e) => {
                const p = e.target.getLatLng();
                void handlePick(p.lat, p.lng);
              },
            }}
          />
        </MapContainer>
      </div>

      {/* ---- readout ---- */}
      <div className="flex items-center justify-between gap-3 text-xs">
        <div className="flex gap-3 text-gray-500">
          <span>
            {t('assess.map.lat')}:{' '}
            <strong className="text-gray-800">{latitude.toFixed(4)}</strong>
          </span>
          <span>
            {t('assess.map.lon')}:{' '}
            <strong className="text-gray-800">{longitude.toFixed(4)}</strong>
          </span>
        </div>
        {place && (
          <span className="text-primary-700 font-medium truncate">
            {t('assess.map.detected')}: {place}
          </span>
        )}
      </div>

      <p className="text-xs text-gray-400">{t('assess.map.tip')}</p>
    </div>
  );
}
