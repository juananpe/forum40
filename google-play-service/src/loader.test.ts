import {connect, IDbApi} from "./db";
import {App, Collection, IScraper, Review} from "./play";
import * as config from "./config";
import {mocked} from "ts-jest/utils";
import { update } from "./loader";
import { asyncIterable } from "./util";
import { collection } from "google-play-scraper";
import { throws } from "assert";

jest.mock('./db');
jest.mock('./config', () => ({
	TRACKED_COLLECTIONS: [
		{collection: 'topselling_free', num: 3},
	],
	REVIEW_MIN_DATE: new Date('2000-01-01T00:00:00Z'),
}));


const minDate = config.REVIEW_MIN_DATE as any as Date;



beforeEach(() => {
	mocked(connect).mockClear();
});



test('should initialize on first start', async () => {
	const mockConnect = mocked(connect).mockImplementation(() => new MockDbApi({
		authenticated: false,
		registered: false,
		sourceExists: false,
		documents: [],
		comments: [],
	}));

	const mockScraper = new MockScraper(playMockData);
	await update(mockScraper);
	
	expect(mockConnect).toHaveBeenCalledTimes(1);
	const dbMock = mockConnect.mock.results[0].value as MockDbApi;

	expect(dbMock.register).toHaveBeenCalled();
	expect(dbMock.createSource).toHaveBeenCalled();
	expect((new Set(dbMock.state.documents)).size).toBe(3);
	expect((new Set(dbMock.state.comments)).size).toBe(3 * (nReviewsPerApp - nOldReviewsPerApp));
});


test('should update on subsequent runs', async () => {
	const loaded = playMockData.apps.slice(0, 2);
	const nLoadedReviewsPerApp = 10;

	const mockConnect = mocked(connect).mockImplementation(() => new MockDbApi({
		authenticated: false,
		registered: true,
		sourceExists: true,
		documents: loaded.map(({app}) => app.appId),
		comments: loaded.flatMap(({reviews}) => reviews.slice(nOldReviewsPerApp, nOldReviewsPerApp + nLoadedReviewsPerApp).map(review => review.id)),
	}));

	const mockScraper = new MockScraper(playMockData);
	await update(mockScraper);
	
	expect(mockConnect).toHaveBeenCalledTimes(1);
	const dbMock = mockConnect.mock.results[0].value as MockDbApi;

	expect(dbMock.register).not.toHaveBeenCalled();
	expect(dbMock.createSource).not.toHaveBeenCalled();
	expect((new Set(dbMock.state.documents)).size).toBe(loaded.length);
	expect(dbMock.createComment).toHaveBeenCalledTimes(loaded.length * (nReviewsPerApp - nOldReviewsPerApp - nLoadedReviewsPerApp + 1)); // only called with new comments +1 to see collision
	expect((new Set(dbMock.state.comments)).size).toBe(loaded.length * (nReviewsPerApp - nOldReviewsPerApp));
});



// Mock play

type MockPlayData = {
	collections: Array<{
		collection: Collection,
		appIds: string[],
	}>,
	apps: Array<{
		app: App,
		reviews: Review[],
	}>
};

class MockScraper implements IScraper {
	data: MockPlayData;

	constructor(data: MockPlayData) {
		this.data = data;
	}

	private getAppEntry = (appId: string) => {
		const entry = this.data.apps.find(entry => entry.app.appId === appId);
		if (!entry) {
			throw Error(`Unknown app id ${appId}`);
		}
		return entry;
	}

	fetchCollection = jest.fn((collection: collection, num: number) => {
		const collObj = this.data.collections.find(collEntry => collEntry.collection === collection);
		if (!collObj) {
			throw Error(`Unknown collection ${collection}`);
		}

		const apps = collObj.appIds
			.slice(0, num)
			.map(appId => this.getAppEntry(appId))
			.map(entry => entry.app);
		
		return Promise.resolve(apps);
	})

	fetchApp = jest.fn((appId: string): Promise<App> => {
		return Promise.resolve(this.getAppEntry(appId).app);
	});

	fetchReviews = jest.fn((appId: string): AsyncIterableIterator<Review> => {
		return asyncIterable(
			this.getAppEntry(appId).reviews
					.slice()  // copy
					.sort((a, b) => Date.parse(b.date) - Date.parse(a.date)));  // newest date first
	});
}

// mock data
const appIds = ['com.example.one', 'com.example.two', 'com.example.three'];
const nReviewsPerApp = 100;
const nOldReviewsPerApp = 20;
const playMockData: MockPlayData = {
	collections: [
		{collection: Collection.TOP_FREE, appIds},
	],
	apps: appIds.map((appId, appIdx) => ({
		app: {
			appId,
			url: `http://example.com/${appId}`,
			title: `App ${appId}`,
			description: `Description for ${appId}`,
			updated: 1612302187000,
		} as Partial<App> as any as App,
		reviews: Array.from({length: nReviewsPerApp}).map((_, reviewIdx) => ({
			id: `${appIdx * nReviewsPerApp + reviewIdx}`,
			date: new Date(minDate.getTime() + (0.5 + reviewIdx - nOldReviewsPerApp) * 5 * 60 * 1000).toISOString(),
			title: 'Title',
			text: 'Review body',
		}) as Partial<Review> as any as Review),
	}))
};


// Mock Forum4.0 backend
interface MockDbState {
	registered: boolean,
	authenticated: boolean,
	sourceExists: boolean,
	documents: string[],
	comments: string[],
}

class MockDbApi implements IDbApi {
	state: MockDbState;
	mock_user = {user: config.USER_NAME, userId: 1, token: 'abc'};

	constructor(state: MockDbState) {
		this.state = state;
	};

	// Authentication
	isAuthenticated = jest.fn(() => this.state.authenticated);
	login = jest.fn(() => {
		if (this.state.registered) {
			this.state.authenticated = true;
			return Promise.resolve({status: 200, data: this.mock_user});
		} else {
			return Promise.resolve({status: 401, data: null});
		}
	});
	register = jest.fn(() => { // registration succeeds
		this.state.authenticated = true;
		return Promise.resolve({status: 200, data: this.mock_user});
	});
	refreshToken = jest.fn();

	// Sources
	getSourceByName = jest.fn(() => Promise.resolve(
		this.state.sourceExists
		? {status: 200, data: {id: 2, protected: false, name: config.SOURCE_NAME, domain: config.SOURCE_DOMAIN}}
		: {status: 404, data: null}
	));
	createSource = jest.fn(() => {
		this.state.sourceExists = true;
		return Promise.resolve({status: 200, data: {id: 2}});
	});

	// Documents
	getDocumentsBySourceId = jest.fn((sourceId: number, limit: number, skip: number) => Promise.resolve({
		status: 200,
		data: this.state.documents.slice(skip, skip+limit).map((externalId, index) => ({
			id: index,
			externalId,
			sourceId: 1,
			url: null,
			title: null,
			timestamp: null,
			category: null,
			metadata: null,
		}))
	}))
	createDocument = jest.fn(({externalId}) => this.insert(this.state.documents, {externalId}));

	// Comments
	createComment = jest.fn(({externalId}) => this.insert(this.state.comments, {externalId, sourceId: 2}));

	// Utils
	insert = <T extends {externalId: string}>(list: string[], obj: T) => {
		const foundIndex = list.indexOf(obj.externalId);
		const found = foundIndex >= 0;
		const index = found ? foundIndex : list.push(obj.externalId)-1;

		return Promise.resolve({
			status: found ? 409 : 200,
			data: {...obj, id: index},
		});
	};
}
