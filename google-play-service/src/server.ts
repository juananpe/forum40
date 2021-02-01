import {fetchCollection, fetchApp, fetchReviews, Collection} from "./play";

const main = async () => {
	console.log(await fetchCollection(Collection.TOP_FREE, 10));
	console.log(await fetchApp('ch.threema.app'));

	const since = new Date();
	since.setDate(since.getDate() - 7);
	const reviews = [];
	for await (const review of fetchReviews('ch.threema.app', since)) {
		reviews.push(review);
	}
	console.log(reviews);
};

main().then(() => console.log('done'));
