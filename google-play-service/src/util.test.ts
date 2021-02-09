import { toCamelCase, toSnakeCase } from "./util";

const snakeCaseObject = {
	auth_token: 'abc',
	user: {
		name: 'Walid',
		is_admin: true,
		saved_topics: [
			{short_title: 'CoLiBERT'},
			{short_title: 'Comment Analysis'},
		]
	}
} as const;

const camelCaseObject = {
	authToken: 'abc',
	user: {
		name: 'Walid',
		isAdmin: true,
		savedTopics: [
			{shortTitle: 'CoLiBERT'},
			{shortTitle: 'Comment Analysis'},
		]
	},
} as const;


test('transform object keys to snake_case', () => {
	expect(toSnakeCase(camelCaseObject))
		.toEqual(snakeCaseObject)
});

test('transform object keys to snake_case', () => {
	expect(toCamelCase(snakeCaseObject))
		.toEqual(camelCaseObject)
});
