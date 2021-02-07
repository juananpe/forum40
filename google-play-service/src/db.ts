import fetch from "node-fetch";
import * as config from "./config";
import { toCamelCase, toSnakeCase } from "./util";


export interface IDbApi {
	// Authentication
	isAuthenticated: () => boolean;
	login: (username: string, password: string) => Promise<Response<AuthResponseData | null>>;
	register: (username: string, password: string) => Promise<Response<AuthResponseData>>;
	refreshToken: () => void;

	// Sources
	getSourceByName: (name: string) => Promise<Response<Source | null>>
	createSource: (source: NewSource) => Promise<Response<CreateSourceResponseData>>;

	// Comments
	createComment: (comment: NewComment) => Promise<Response<CreateCommentResponseData>>;

	// Documents
	createDocument: (document: NewDocument) => Promise<Response<CreateDocumentResponseData>>;
};

export const connect = (): IDbApi => {
	return new DbApi();
}


class DbApi implements IDbApi {
	private apiKey: string | null;
	private authRefreshTimeoutId: NodeJS.Timeout | null;

	constructor() {
		this.apiKey = null;
		this.authRefreshTimeoutId = null;
	}


	// Basic communication

	private get = <T>(path: string): Promise<Response<T>> => {
		return this.call(path);
	};

	private post = <T>(path: string, data?: any): Promise<Response<T>> => {
		return this.call(path, 'POST', data);
	};

	private call = async <T>(path: string, method: string = 'GET', data?: any): Promise<Response<T>> => {
		const url = `${config.API_BASE_URL}/db${path}`;

		const res = await fetch(url, {
			method,
			body: data ? JSON.stringify(toSnakeCase(data)) : undefined,
			headers: {
				...(this.apiKey ? {'X-Access-Token': this.apiKey} : {}),
				...(data ? {'Content-Type': 'application/json'} :  {}),
			},
		});

		let responseData = null;
		try {
			responseData = toCamelCase(await res.json());
		} catch (error) {};

		return {
			status: res.status,
			data: responseData,
		}
	};


	// Authentication

	isAuthenticated = (): boolean => {
		return this.apiKey !== null;
	}

	register = async (username: string, password: string) => {
		const response = await this.post<AuthResponseData>('/auth/register', {username, password});
		this.handleAuthResponse(response);
		return response;
	};

	login = async (username: string, password: string) => {
		const response = await this.get<AuthResponseData>(`/auth/login/${username}/${password}`);
		this.handleAuthResponse(response);
		return response;
	};

	refreshToken = async () => {
		const response = await this.get<AuthResponseData>(`/auth/refreshToken/`);
		this.handleAuthResponse(response);
		return response;
	}

	private handleAuthResponse = (response: Response<AuthResponseData>) => {
		if (this.authRefreshTimeoutId) {
			clearTimeout(this.authRefreshTimeoutId);
			this.authRefreshTimeoutId = null;
		}

		if (response.status >= 200 && response.status < 300 && response.data.token) {
			this.apiKey = response.data.token;
			this.authRefreshTimeoutId = setTimeout(() => this.refreshToken(), config.AUTH_REFRESH_INTERVAL);
		} else {
			this.apiKey = null;
		}
	};



	// Sources

	getSourceByName = (name: string) => {
		return this.get<Source | null>(`/sources/${name}`);
	};

	createSource = (source: NewSource) => {
		return this.post<CreateSourceResponseData>('/sources/', source);
	};


	// Comments

	createComment = (comment: NewComment) => {
		return this.post<CreateCommentResponseData>('/comments/', comment);
	};


	// Documents

	createDocument = (document: NewDocument) => {
		return this.post<CreateDocumentResponseData>('/documents/', document);
	};
};


export interface Response<T> {
	status: number,
	data: T,
};


// Authentication

export interface AuthResponseData {
	user: string,
	userId: number,
	token: string,
};



// Sources

export interface NewSource {
	name: string,
	domain: string,
}

export interface Source extends NewSource {
	id: number,
	protected: boolean,
}

export interface CreateSourceResponseData {
	id: number,
}


// Comments

export interface NewComment {
	docId?: number | null,
	sourceId: number,
	userId?: number | null,
	parentCommentId?: number | null,
	status?: string | null,
	title: string,
	text: string,
	embedding?: string | null,
	timestamp?: string | null,
	externalId: string, // TODO: Make required in backend
};

export interface CreateCommentResponseData {
	id: number,
	sourceId: number,
	externalId: string,
};


// Documents

export interface NewDocument {
	url: string,
	title: string,
	text: string,
	timestamp: string,
	metadata?: string | null,
	sourceId: number,
	externalId: string,
}

export interface CreateDocumentResponseData {
	id: number,
};

