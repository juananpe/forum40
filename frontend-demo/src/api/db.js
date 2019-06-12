import axios from "axios";

const API_URL = process.env.VUE_APP_ROOT_API

export const Endpoint = {
    LABELS: "db/labels",
    COMMENTS: 'db/comments',
    COMMENTS_COUNT: 'db/comments/count',
    COMMENTS_PARENTS: (commentId) => `db/comments/parent_recursive/${commentId}`,
    TIMESERIES: 'db/comments/timeseries',
    TIMESERIES_MULTI: 'db/comments/timeseries_multi',
    TEST_LOGIN: 'db/auth/test',
    REFRESH_TOKEN: 'db/auth/refreshToken',
    LOGIN: (username, password) => `db/auth/login/${username}/${password}`,
    LOGOUT: 'db/auth/logout'
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

}

export default Service;
