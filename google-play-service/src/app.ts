import {update} from "./loader";
import * as config from "./config";
import { Scraper } from "./play";

const main = async () => {
	const play = new Scraper({
		lang: config.LANG,
		country: config.COUNTRY,
		throttle: config.THROTTLE || undefined,
	})

	await update(play);
	console.log('done');
}

main();
