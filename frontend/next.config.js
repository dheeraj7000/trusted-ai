/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production (docker), NEXT_PUBLIC_API_URL is set and the client
    // calls the backend directly - no proxy needed.  For local dev the
    // proxy rewrite forwards /api/* to the local uvicorn server.
    if (process.env.NEXT_PUBLIC_API_URL) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};
module.exports = nextConfig;