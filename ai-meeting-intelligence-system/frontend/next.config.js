/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Same-origin `/api/backend/*` → FastAPI (`NEXT_PUBLIC_API_BASE=/api/backend` in .env.local).
    // Avoids browser CORS issues when the UI and API differ by hostname/port.
    const dest = (
      process.env.BACKEND_REWRITE_URL ||
      "http://127.0.0.1:8000"
    ).replace(/\/$/, "");
    return [
      {
        source: "/api/backend/:path*",
        destination: `${dest}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

