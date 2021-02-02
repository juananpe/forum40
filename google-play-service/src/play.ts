import gplay from "google-play-scraper";
import * as config from "./config";

export import Collection = gplay.collection;

const baseOpts = {
	lang: config.LANG,
	country: config.COUNTRY,
	throttle: config.THROTTLE || undefined,
}

export function fetchCollection(collection: Collection, num: number) {
	return gplay.list({
		...baseOpts,
		collection,
		num,
	});
}

export function fetchApp(appId: string) {
	return gplay.app({
		...baseOpts,
		appId,
	});
};

export async function* fetchReviews(appId: string, since?: Date) {
	let paginationToken = null;
	while (true) {
		const {data, nextPaginationToken} = await gplay.reviews({
			...baseOpts,
			appId,
			sort: gplay.sort.NEWEST,
			paginate: true,
			nextPaginationToken: paginationToken || undefined,
		}) as any as {data: gplay.IReviewsItem[], nextPaginationToken: string};
		// ^ typings in google-play-scraper are outdated (as of 2021-02-01)
		paginationToken = nextPaginationToken;

		const reviews = since ? data.filter(({date}) => new Date(date) >= since) : data;
		yield* reviews;
		if (reviews.length < data.length || reviews.length === 0 || nextPaginationToken === null) {
			return;
		}
	};
}
