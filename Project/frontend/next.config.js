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
