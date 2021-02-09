import gplay from "google-play-scraper";
import {Collection, App, AppBase, Review} from "./types";


export interface IScraper {
	fetchCollection: (collection: Collection, num: number) =>  Promise<AppBase[]>;
	fetchApp: (appId: string) => Promise<App>
	fetchReviews: (appId: string) => AsyncIterableIterator<Review>;
}


export interface ScraperBaseOptions {
	lang: string,
	country: string,
	throttle?: number,
}

export class Scraper {
	baseOpts: ScraperBaseOptions

	constructor(baseOpts: ScraperBaseOptions) {
		this.baseOpts = baseOpts;
	}

	fetchCollection(collection: Collection, num: number): Promise<AppBase[]> {
		return gplay.list({
			...this.baseOpts,
			collection,
			num,
		});
	}

	fetchApp(appId: string): Promise<App> {
		return gplay.app({
			...this.baseOpts,
			appId,
		});
	};
	
	async * fetchReviews(appId: string): AsyncIterableIterator<Review> {
		let paginationToken = null;
		while (true) {
			const {data: reviews, nextPaginationToken} = await gplay.reviews({
				...this.baseOpts,
				appId,
				sort: gplay.sort.NEWEST,
				paginate: true,
				nextPaginationToken: paginationToken || undefined,
			}) as any as {data: gplay.IReviewsItem[], nextPaginationToken: string};
			// ^ typings in google-play-scraper are outdated (as of 2021-02-01)
			paginationToken = nextPaginationToken;
	
			yield* reviews;
			if (reviews.length === 0 || nextPaginationToken === null) {
				return;
			}
		};
	}
}


