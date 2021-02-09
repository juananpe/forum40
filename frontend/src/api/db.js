import axios from "axios";
import store from "../store";
import { Getters } from "../store/const";

export const API_URL = process.env.VUE_APP_ROOT_API

export const Endpoint = {
    LABELS: (source_id) => `db/labels/${source_id}`,
    ADD_LABEL: (name, source_id) => `db/labels/binary/${name}/${source_id}`,
    COMMENTS: 'db/comments/',
    COMMENT_DOCUMENT: (comment_id) => `db/comments/${comment_id}/document`,
    COMMENTS_TIME_HISTOGRAM: "db/comments/time_histogram",
    SOURCES: "db/sources/",
    ADD_ANNOTATION_TO_COMMENT: (comment_id, label_id, label) => `db/annotations/${comment_id}/${label_id}/${label}`,
    COMMENTS_PARENTS: (commentId) => `db/comments/parent_recursive/${commentId}`,
    COMMENTS_SIMILAR: (commentId) => `similarity/embeddings/comments/${commentId}/similar`,
    TEST_LOGIN: 'db/auth/test',
    REFRESH_TOKEN: 'db/auth/refreshToken',
    LOGIN: (username, password) => `db/auth/login/${username}/${password}`,
    MODELS: (labelId) => `db/models/${labelId}`,
    CATEGORIES: (labelId) => `db/documents/categories/${labelId}`
}

const client = axios.create({
    baseURL: process.env.VUE_APP_ROOT_API
});

client.interceptors.request.use(config => {
    const jwt = store.getters[Getters.jwt];

    return {
        ...config,
        headers: {
            ...(jwt ? {'X-Access-Token': jwt} : {}),
            ...(config.headers || {}),
        }
    }
});

class Service {
    static get(path) {
        return client.get(path);
    }

    static async post(path, payload) {
        return client.post(path, payload);
    }

    static async put(path, payload) {
        return client.put(path, payload);
    }
}

export default Service;
