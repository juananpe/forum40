import { camelCase, snakeCase } from "change-case";

export const mapObjectKeysDeep = (val: any, transformFn: (key: string) => string): any => {
	if (Array.isArray(val)) {
		return val.map(item => mapObjectKeysDeep(item, transformFn));
	} else if (typeof val === 'object' && val !== null) {
		return Object.fromEntries(
			Object.entries(val).map(([itemKey, itemVal]) => [
				transformFn(itemKey),
				mapObjectKeysDeep(itemVal, transformFn),
			]),
		);
	} else {
		return val;
	}
};

export const toSnakeCase = (val: any): any => {
	return mapObjectKeysDeep(val, key => snakeCase(key));
};

export const toCamelCase = (val: any): any => {
	return mapObjectKeysDeep(val, key => camelCase(key));
};


export async function* asyncIterable<T>(items: T[]) {
	yield* items;
}

