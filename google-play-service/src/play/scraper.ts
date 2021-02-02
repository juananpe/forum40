import gplay from "google-play-scraper";
import * as config from "../config";
import {Collection, App, AppBase, Review} from "./types";


const baseOpts = {
	lang: config.LANG,
	country: config.COUNTRY,
	throttle: config.THROTTLE || undefined,
}

export function fetchCollection(collection: Collection, num: number): Promise<AppBase[]> {
	return gplay.list({
		...baseOpts,
		collection,
		num,
	});
}

export function fetchApp(appId: string): Promise<App> {
	return gplay.app({
		...baseOpts,
		appId,
	});
};

export async function* fetchReviews(appId: string): AsyncIterableIterator<Review> {
	let paginationToken = null;
	while (true) {
		const {data: reviews, nextPaginationToken} = await gplay.reviews({
			...baseOpts,
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
