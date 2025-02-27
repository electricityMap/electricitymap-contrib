// Generates a static sitemap for the app based on the zones in the config file

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import zonesConfig from '../config/zones.json' with { type: 'json' };

// Import this from the constant file when this script is in typescript
const urlTimeRanges = ['24h', '72h', '30d', '12mo', 'all'];

// Fix the paths for Windows/Linux consistency
let dirname = path.dirname(fileURLToPath(import.meta.url));

const __dirname = decodeURIComponent(dirname);
const SITEMAP_DIR = path.join(__dirname, '..', 'public');
const SITEMAP_PATH = path.join(SITEMAP_DIR, 'sitemap.xml');

function generateSitemap() {
  // Ensure the directory exists
  if (!fs.existsSync(SITEMAP_DIR)) {
    try {
      fs.mkdirSync(SITEMAP_DIR, { recursive: true });
      console.log('Directory created:', SITEMAP_DIR);
    } catch (error) {
      console.error('Failed to create directory:', error);
      return;
    }
  }

  const mapUrls = urlTimeRanges.map(
    (timeRange) =>
      `<url><loc>https://app.electricitymaps.com/map/${timeRange}</loc></url>`
  );

  const zoneUrls = Object.keys(zonesConfig.zones).flatMap((zone) =>
    urlTimeRanges.map(
      (timeRange) =>
        `<url><loc>https://app.electricitymaps.com/zone/${zone}/${timeRange}</loc></url>`
    )
  );

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
  <urlset xmlns="https://www.sitemaps.org/schemas/sitemap/0.9">
    ${[...mapUrls, ...zoneUrls].join('')}
  </urlset>`.replaceAll(/\n\s*/g, '');

  fs.writeFileSync(SITEMAP_PATH, sitemap);
}

generateSitemap();
