/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const API = process.env.NEXT_PUBLIC_API_URL || 'https://uznpuu-production.up.railway.app';
    return [
      { source: '/api/:path*',    destination: `${API}/api/:path*` },
      { source: '/ask',           destination: `${API}/ask` },
      { source: '/static/:path*', destination: `${API}/static/:path*` },
    ];
  },
};

module.exports = nextConfig;
