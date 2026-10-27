/** @type {import('next').NextConfig} */

/**
 * Where the FastAPI backend lives, as seen from the Next.js
 * server (not from the browser).
 */
const API_TARGET =
  process.env.API_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,

  // Empty string => the browser calls same-origin /api/*, which
  // the rewrite below forwards to the backend. That removes CORS
  // from the picture entirely and stops browser code from ever
  // dialling localhost directly.
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
    // CARTO basemaps key. Next only auto-inlines NEXT_PUBLIC_* into
    // browser code, so this name is deliberately un-prefixed and
    // forwarded to the client by listing it here. That is substitution,
    // not protection: the value still ships in the bundle (it has to —
    // Leaflet puts it in the tile URL), so treat it as public and rely
    // on CARTO's rate limits. Must be present at BUILD time, i.e. set
    // before `npm run build` / a Vercel deploy.
    CARTO_BASEMAPS_KEY: process.env.CARTO_BASEMAPS_KEY || '',
  },

  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_TARGET}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
