import {update} from "./loader";
import * as config from "./config";
import { Scraper } from "./play";

const main = async () => {
	const scraper = new Scraper({
		lang: config.LANG,
		country: config.COUNTRY,
		throttle: config.THROTTLE || undefined,
	});

	update(scraper);

	setInterval(
		() => update(scraper),
		config.UPDATE_INTERVAL,
	);
}

main();
