/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['enet2.s3.amazonaws.com'], // Add your S3 bucket domain here
  },
  basePath: '/client_portal', // If your app has a base path
};

export default nextConfig;
