import axios from "axios";

const API_URL = process.env.VUE_APP_ROOT_API

class Service {

    static get(path, callback) {
        return axios.get(`${API_URL}${path}`).then(
            (response) => callback(response.status, response.data)
          );
      }

    static post(path, payload, callback) {
        return axios.post(`${API_URL}${path}`, payload).then((response) => callback(response.status, response.data));
    }

}

export default Service;
