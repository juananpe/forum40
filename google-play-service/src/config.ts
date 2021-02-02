import { Collection } from "./play";

export const LANG = process.env['LANG'] || 'en';
export const COUNTRY = process.env['COUNTRY'] || 'us';
export const THROTTLE = process.env['MAX_REQUESTS_PER_SECOND'] ? parseInt(process.env['MAX_REQUESTS_PER_SECOND']) : null;
export const API_BASE_URL = 'http://backend/api';
export const AUTH_REFRESH_INTERVAL = 5 * 60 * 1000;
export const USER_NAME = 'google-play-service';
export const USER_PASSWORD = 'abc';  // TODO: Docker secrets
export const SOURCE_NAME = 'Google Play';
export const SOURCE_DOMAIN = 'https://play.google.com/';
export const TRACKED_COLLECTIONS: TrackedCollection[] = [
	{collection: Collection.TOP_FREE, num: 5},
	{collection: Collection.TOP_PAID, num: 5},
];
export const REVIEW_MIN_DATE: Date | null = process.env['REVIEW_MIN_DATE'] ? new Date(process.env['REVIEW_MIN_DATE']) : null



export interface TrackedCollection {
	collection: Collection,
	num: number,
};
