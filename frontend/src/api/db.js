import axios from "axios";
import store from "../store";
import { Getters } from "../store/const";
import Qs from "qs";


const client = axios.create({
    baseURL: process.env.VUE_APP_ROOT_API,
    paramsSerializer: (params) => 
        Qs.stringify(params, {
            arrayFormat: 'repeat',
            skipNulls: true,
        }),
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

const service = {
    login: (username, password) =>
        client.get(`/db/auth/login/${username}/${password}`),

    refreshToken: () =>
        client.get(`/db/auth/refreshToken`),

    testLogin: () =>
        client.get(`/db/auth/test`),

    getModels: (labelId) =>
        client.get(`/db/models/${labelId}`),

    getCommentDocument: (commentId) =>
        client.get(`/db/comments/${commentId}/document`),

    getSources: () =>
        client.get(`/db/sources/`),

    getLabels: (sourceId) =>
        client.get(`/db/labels/${sourceId}`),

    createLabel: (sourceId, name, description) =>
        client.put(`/db/labels/binary/${name}/${sourceId}`, {description}),

    getCategories: (labelId) =>
        client.get(`/db/documents/categories/${labelId}`),

    annotateComment: (commentId, labelId, label) => 
        client.put(`/db/annotations/${commentId}/${labelId}/${Number(label)}`),
    
    getSimilarComments: (commentId) =>
        client.get(`/similarity/embeddings/comments/${commentId}/similar`),

    getParentComments: (commentId) =>
        client.get(`/db/comments/parent_recursive/${commentId}`),

    getTimeHistogram: (sourceId, {labelId, granularity, keywords}) =>
        client.get(`/db/comments/time_histogram`, {
            params: {
                source_id: sourceId,
                label: labelId,
                granularity: granularity,
                keyword: keywords,
            }
        }),
    
    getComments: (sourceId, {labelIds, keywords, skip, limit, labelSortId, order, category}) =>
        client.get(`/db/comments/`, {
            params: {
                label: labelIds,
                source_id: sourceId,
                keyword: keywords,
                skip: skip,
                limit: limit,
                order: order,
                label_sort_id: labelSortId,
                category: category,
            }
        }),
}

export default service;
