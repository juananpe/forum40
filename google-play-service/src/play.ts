import gplay from "google-play-scraper";
import * as config from "./config";

export import Collection = gplay.collection;


export function fetchCollection(collection: Collection, num: number) {
	return gplay.list({
		collection,
		num,
		lang: config.LANG,
		country: config.COUNTRY,
	});
}

export function fetchApp(appId: string) {
	return gplay.app({
		appId,
		lang: config.LANG,
		country: config.COUNTRY,
	});
};

export async function* fetchReviews(appId: string, since?: Date) {
	let paginationToken = null;
	while (true) {
		const {data, nextPaginationToken} = await gplay.reviews({
			appId,
			sort: gplay.sort.NEWEST,
			paginate: true,
			nextPaginationToken: paginationToken || undefined,
			lang: config.LANG,
			country: config.COUNTRY,
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
