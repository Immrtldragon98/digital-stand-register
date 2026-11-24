/** @type {import('next').NextConfig} */
const staticExport = process.env.DSR_STATIC_EXPORT === "1";
const nextConfig = {
  ...(staticExport ? { output: "export", trailingSlash: true, images: { unoptimized: true } } : {}),
  reactStrictMode: true,
  poweredByHeader: false,
  // Preserve FastAPI collection URLs ending in `/` so its redirects cannot
  // send browser requests from the frontend origin to the API origin.
  skipTrailingSlashRedirect: true,
  ...(!staticExport ? { async rewrites() {
    // Browser requests stay on the frontend origin; Render supplies the API origin.
    const apiOrigin = (process.env.DSR_API_ORIGIN || "http://localhost:8000").replace(/\/$/, "");
    return [
      { source: "/api/v1/:path*/", destination: `${apiOrigin}/api/v1/:path*/` },
      { source: "/api/v1/:path*", destination: `${apiOrigin}/api/v1/:path*` },
    ];
  } } : {}),
};

module.exports = nextConfig;
