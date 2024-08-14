/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/client_portal',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.enet2.com',
        port: '',
        pathname: '/public/**',
      },
    ],
  },
};

export default nextConfig;
