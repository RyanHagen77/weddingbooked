/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/client_portal',
  images: {
    domains: ['www.enet2.com', 'enet2.cloudfront.net'], // Add all allowed domains here
  },
  reactStrictMode: true,
  swcMinify: true,
};

export default nextConfig;
