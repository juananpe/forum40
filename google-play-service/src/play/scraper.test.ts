import {mocked} from 'ts-jest/utils';
import {fetchReviews} from './scraper';
import * as gplay from 'google-play-scraper';
jest.mock('google-play-scraper');


describe('fetch reviews', () => {
	const reviews = Array.from({length: 127}).map(() => Symbol());
	const pages = [
		{token: undefined, nextToken: 'a', reviews: reviews.slice(0, 50)},
		{token: 'a', nextToken: 'b', reviews: reviews.slice(50, 100)},
		{token: 'b', nextToken: null, reviews: reviews.slice(100, 127)},
	];

	beforeAll(() => {
		mocked(gplay.reviews)
			.mockImplementation(({paginate, nextPaginationToken}) => {
				expect(paginate).toBeTruthy();
	
				const page = pages.find(page => page.token === nextPaginationToken);
				if (!page) {
					fail('Select invalid page');
				}
				
				return Promise.resolve({
					data: page.reviews,
					nextPaginationToken: page.nextToken,
				} as any);
			});
	});

	beforeEach(() => {
		mocked(gplay.reviews).mockClear();
	});

	test('should return all reviews', async () => {
		let index = 0;
		for await (const review of fetchReviews('com.jest.example')) {
			expect(review).toBe(reviews[index]);
			index += 1
		};
	});

	test('should only fetch required pages', async () => {
		let index = 0;
		for await (const review of fetchReviews('com.jest.example')) {
			if (index === 60) {
				break;
			}
			index += 1;
		}
	
		expect(mocked(gplay.reviews)).toHaveBeenCalledTimes(2);
	});
})

