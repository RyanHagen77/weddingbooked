/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/client_portal',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'www.enet2.com',
        port: '',
        pathname: '/media/**', // Adjust this path to match where your images are served from
      },
    ],
  },
};

export default nextConfig;
