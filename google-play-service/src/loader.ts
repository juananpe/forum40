import * as config from "./config";
import {BaseDocument, connect, IDbApi} from "./db";
import { IScraper } from "./play";


export const update = async (play: IScraper) => {
	console.log('Updating reviews from Google Play Store')
	if (config.REVIEW_MIN_DATE !== null) {
		console.log(`Will not load reviews written before ${config.REVIEW_MIN_DATE.toUTCString()}`)
	}

	const api = connect()
	await loginOrRegister(api);
	const {sourceId, tracked} = await loadOrInitializeSource(play, api);

	console.log(`Updating reviews for ${tracked.length} apps`)
	for (const {appId, documentId} of tracked) {
		await insertNewReviews(play, api, appId, sourceId, documentId);
	}

	console.log('Triggering embedding and reindexing')
	await api.embed(sourceId);
	await api.index(sourceId);
};


// Authentication

const loginOrRegister = async (api: IDbApi) => {
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

const loadOrInitializeSource = async (play: IScraper, api: IDbApi): Promise<SourceTrackingData> => {
	const loadedSource = await loadSource(api);
	if (loadedSource) {
		return loadedSource;
	}

	return initializeSource(play, api);
};

const loadSource = async (api: IDbApi): Promise<SourceTrackingData | null> => {
	const {data: source} = await api.getSourceByName(config.SOURCE_NAME);
	if (!source) {
		return null;
	}

	const documents = await getAllSourceDocuments(api, source.id);
	const tracked = documents.flatMap(doc => !doc.externalId ? [] : [{
		documentId: doc.id,
		appId: doc.externalId,
	}]);

	return {
		sourceId: source.id,
		tracked,
	};
};

const getAllSourceDocuments = async (api: IDbApi, sourceId: number): Promise<BaseDocument[]> => {
	const pageSize = 100;
	const documents: BaseDocument[] = []
	for (let pageIndex = 0;; pageIndex += 1) {
		const {data} = await api.getDocumentsBySourceId(sourceId, pageSize, pageIndex*pageSize);
		documents.push(...data)

		if (data.length < pageSize) {
			return documents;
		}
	}
}

const initializeSource = async (play: IScraper, api: IDbApi): Promise<SourceTrackingData> => {
	const {data: source} = await api.createSource({
		name: config.SOURCE_NAME,
		domain: config.SOURCE_DOMAIN,
	});
	const tracked = await insertAppsFromTrackedCollections(play, api, source.id);

	return {
		sourceId: source.id,
		tracked,
	}
}

const insertAppsFromTrackedCollections = async (play: IScraper, api: IDbApi, sourceId: number): Promise<TrackItem[]> => {
	const tracked: TrackItem[] = [];
	for (const {collection, num} of config.TRACKED_COLLECTIONS) {
		const apps = await play.fetchCollection(collection, num);
		console.log(`Will track ${apps.length} apps from collection ${collection}:`, apps.map(app => app.appId));
		for (const baseApp of apps) {
			const {appId, url, title, description, updated, genre, ...metadata} = await play.fetchApp(baseApp.appId);

			const {data: document} = await api.createDocument({
				url,
				externalId: appId,
				sourceId,
				text: description,
				title,
				timestamp: new Date(updated).toISOString(),
				category: genre,
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

const insertNewReviews = async (play: IScraper, api: IDbApi, appId: string, sourceId: number, documentId: number) => {
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
	
	console.log(`Finished update of ${appId}. Inserted ${insertedCount} new reviews.`)
}
