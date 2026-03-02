/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
  // For development: use default server-side rendering
  // For production static export, set output: 'export' in next.config.prod.js
};

export default nextConfig;
