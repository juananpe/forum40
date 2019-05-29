import axios from "axios";

const API_URL = process.env.VUE_APP_ROOT_API

class Service {

    static async get(path) {
        return await axios.get(`${API_URL}${path}`);
    }

    static async post(path, payload) {
        return await axios.post(`${API_URL}${path}`, payload);
    }

}

export default Service;
