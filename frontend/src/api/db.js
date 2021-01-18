import axios from "axios";

export const API_URL = process.env.VUE_APP_ROOT_API

export const Endpoint = {
    LABELS: (source_id) => `db/labels/${source_id}`,
    ADD_LABEL: (name, source_id) => `db/labels/binary/${name}/${source_id}`,
    COMMENTS: 'db/comments/',
    COMMENT_ID: (comment_id, labels) => `db/comments/${comment_id}?${labels}`,
    COMMENTS_TIME_HISTOGRAM: "db/comments/time_histogram",
    SOURCES: "db/sources/",
    ADD_ANNOTATION_TO_COMMENT: (comment_id, label_id, label) => `db/annotations/${comment_id}/${label_id}/${label}`,
    COMMENTS_COUNT: 'db/comments/count',
    COMMENTS_PARENTS: (commentId) => `db/comments/parent_recursive/${commentId}`,
    COMMENTS_SIMILAR: (commentId) => `similarity/embeddings/comments/${commentId}/similar`,
    TIMESERIES: 'db/comments/timeseries',
    TIMESERIES_MULTI: 'db/comments/timeseries_multi',
    TEST_LOGIN: 'db/auth/test',
    REFRESH_TOKEN: 'db/auth/refreshToken',
    LOGIN: (username, password) => `db/auth/login/${username}/${password}`,
    LOGOUT: 'db/auth/logout',
    MODELS: (labelId) => `db/models/${labelId}`,
    CATEGORIES: (labelId) => `db/documents/categories/${labelId}`
}

class Service {

    static async get(path, jwt) {
        if (jwt)
            return await axios.get(`${API_URL}${path}`, { headers: { "x-access-token": `${jwt}` } });
        else
            return await axios.get(`${API_URL}${path}`);
    }

    static async post(path, payload, jwt) {
        if (jwt)
            return await axios.post(`${API_URL}${path}`, payload, { headers: { "x-access-token": `${jwt}` } });
        else
            return await axios.post(`${API_URL}${path}`, payload);
    }

    static async put(path, payload, jwt) {
        if (jwt)
            return await axios.put(`${API_URL}${path}`, payload, { headers: { "x-access-token": `${jwt}` } });
        else
            return await axios.put(`${API_URL}${path}`, payload);
    }

}

export default Service;
