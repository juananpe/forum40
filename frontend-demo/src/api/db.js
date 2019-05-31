import axios from "axios";

let user = store.getters.user;

const API_URL = process.env.VUE_APP_ROOT_API

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
