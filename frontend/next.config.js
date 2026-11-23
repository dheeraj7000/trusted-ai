/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Always proxy /api/* to the backend.  In production the backend is
    // reachable from the Next.js container via the ALB on port 8000.
    const backendUrl =
      process.env.BACKEND_URL || "http://agentproof-alb-72725573.us-west-2.elb.amazonaws.com:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};
module.exports = nextConfig;