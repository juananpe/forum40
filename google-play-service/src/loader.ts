import * as config from "./config";
import { DbApi } from "./db";
import * as play from "./play";


export const update = async () => {
	console.log('Updating reviews from Google Play Store')
	if (config.REVIEW_MIN_DATE !== null) {
		console.log(`Will not load reviews written before ${config.REVIEW_MIN_DATE.toUTCString()}`)
	}

	const api = new DbApi()
	await loginOrRegister(api);
	const {sourceId, tracked} = await loadOrInitializeSource(api);

	console.log(`Updating reviews for ${tracked.length} apps`)
	for (const {appId, documentId} of tracked) {
		await insertNewReviews(api, appId, sourceId, documentId);
	}
};


// Authentication

const loginOrRegister = async (api: DbApi) => {
	await api.login(config.USER_NAME, config.USER_PASSWORD);
	if (api.isAuthenticated()) {
		return;
	}

	await api.register(config.USER_NAME, config.USER_PASSWORD);
	if (!api.isAuthenticated()) {
		throw Error('Both login and registration failed');
	}
};


// Source and documents

const loadOrInitializeSource = async (api: DbApi): Promise<SourceTrackingData> => {
	const loadedSource = await loadSource(api);
	if (loadedSource) {
		return loadedSource;
	}

	return initializeSource(api);
};

const loadSource = async (api: DbApi): Promise<SourceTrackingData | null> => {
	const {data: source} = await api.getSourceByName(config.SOURCE_NAME);
	if (!source) {
		return null;
	}
	
	return {
		sourceId: source.id,
		tracked: [],  // TODO: Load all document external ids to find which apps are currently tracked in database
	};
};

const initializeSource = async (api: DbApi): Promise<SourceTrackingData> => {
	const {data: source} = await api.createSource({
		name: config.SOURCE_NAME,
		domain: config.SOURCE_DOMAIN,
	});
	const tracked = await insertAppsFromTrackedCollections(api, source.id);

	return {
		sourceId: source.id,
		tracked,
	}
}

const insertAppsFromTrackedCollections = async (api: DbApi, sourceId: number): Promise<TrackItem[]> => {
	const tracked: TrackItem[] = [];
	for (const {collection, num} of config.TRACKED_COLLECTIONS) {
		const apps = await play.fetchCollection(collection, num);
		console.log(`Will track ${apps.length} apps from collection ${apps}`, apps.map(app => app.appId));
		for (const baseApp of apps) {
			const {appId, url, title, description, updated, ...metadata} = await play.fetchApp(baseApp.appId);

			const {data: document} = await api.createDocument({
				// TODO: category, markup
				url,
				externalId: appId,
				sourceId,
				text: description,
				title,
				timestamp: new Date(updated).toISOString(),
				metadata: JSON.stringify(metadata),
			});
			
			tracked.push({
				appId,
				documentId: document.id
			})
		}
	}

	return tracked;
}

interface SourceTrackingData {
	sourceId: number,
	tracked: TrackItem[],
}

interface TrackItem {
	appId: string,
	documentId: number,
}


// Reviews

const insertNewReviews = async (api: DbApi, appId: string, sourceId: number, documentId: number) => {
	console.log(`Updating reviews for ${appId}`);

	let insertedCount = 0;
	for await (const review of play.fetchReviews(appId)) {
		if (config.REVIEW_MIN_DATE && new Date(review.date) <= config.REVIEW_MIN_DATE) {
			break;
		}

		const {status} = await api.createComment({
			sourceId,
			title: review.title,
			text: review.text,
			docId: documentId,
			externalId: review.id,
			timestamp: review.date,
		});

		if (status === 409) {
			// CONFLICT, comment already exists in backend
			// fetchReviews returns reviews ordered from newest to oldest
			// => reached the newest comment of last crawl
			break;
		}

		insertedCount += 1;
	}
	
	console.log(`Finished update of ${appId}. Inserted new ${insertedCount} reviews.`)
}
