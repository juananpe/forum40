export const LANG = process.env['LANG'] || 'en';
export const COUNTRY = process.env['COUNTRY'] || 'us';
export const THROTTLE = process.env['MAX_REQUESTS_PER_SECOND'] ? parseInt(process.env['MAX_REQUESTS_PER_SECOND']) : null;
export const API_BASE_URL = 'http://backend/api';
export const AUTH_REFRESH_INTERVAL = 5 * 60 * 1000;
