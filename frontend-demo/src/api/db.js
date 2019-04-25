import axios from "axios";

const API_URL = process.env.VUE_APP_ROOT_API

class Service {

    static async get(path, callback) {
        return await axios.get(`${API_URL}${path}`).then(
            (response) => callback(response.status, response.data)
          );
      }

    static async post(path, payload, callback) {
        return await axios.post(`${API_URL}${path}`, payload).then(
            (response) => callback(response.status, response.data)
        );
    }

}

export default Service;
