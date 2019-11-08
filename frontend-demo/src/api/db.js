import axios from "axios";

const API_URL = process.env.VUE_APP_ROOT_API

export const Endpoint = {
    LABELS: "db/labels/",
    ADD_LABEL: (description) => `db/labels/binary/${description}`,
    COMMENTS: 'db/comments/',
    COMMENT_ID: (comment_id, labels) => `db/comments/${comment_id}?${labels}`,
    COMMENTS_GROUP_BY_DAY: "db/comments/groupByDay",
    COMMENTS_GROUP_BY_MONTH: "db/comments/groupByMonth",
    COMMENTS_GROUP_BY_YEAR: "db/comments/groupByYear",
    ADD_ANNOTATION_TO_COMMENT: (comment_id, label_id, label) => `db/annotations/${comment_id}/${label_id}/${label}`,
    COMMENTS_COUNT: 'db/comments/count',
    COMMENTS_PARENTS: (commentId) => `db/comments/parent_recursive/${commentId}`,
    COMMENTS_SIMILAR: `embedding/similar-ids`,
    TIMESERIES: 'db/comments/timeseries',
    TIMESERIES_MULTI: 'db/comments/timeseries_multi',
    TEST_LOGIN: 'db/auth/test',
    REFRESH_TOKEN: 'db/auth/refreshToken',
    LOGIN: (username, password) => `db/auth/login/${username}/${password}`,
    LOGOUT: 'db/auth/logout',
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
