/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/client_portal',
  images: {
    domains: ['www.enet2.com'],
  },
  reactStrictMode: true,
  swcMinify: true,
};

export default nextConfig;
