import { Actions, Mutations } from './const'
import Const from '../const'
import Service, {Endpoint} from '../api/db'

export default {
    [Actions.login]: async function ({ commit, getters, state, dispatch }, { username, password }) {
        try {
            const { data } = await Service.get(Endpoint.LOGIN(username, password));
            commit(Mutations.setJWT, data.token);
            state.refreshTokenInterval = setInterval(() => {
                if ((getters.jwtExpiration * 1000 - state.now) <= Const.refreshTokenBefore)
                    dispatch(Actions.refreshToken);
            }, Const.refreshTokenCheckInterval);
            return true;
        }
        catch (error) {
            const status = error.response.status;
            if (status === 401) {
                return false;
            }
        }
    },
    [Actions.refreshToken]: async function ({ commit, state }) {
        const { data } = await Service.get(Endpoint.REFRESH_TOKEN, state.currentJWT);
        if (data.token) {
            commit(Mutations.setJWT, data.token);
            return true;
        }
        return false;
    },
    [Actions.logout]: async function ({ commit, state }) {
        const { data } = await Service.get(Endpoint.LOGOUT, state.currentJWT);
        if (data.logout === "ok") {
            commit(Mutations.setJWT, '');
            clearInterval(state.refreshTokenInterval);
        }
    },
    [Actions.start]: function ({ commit }) {
        setInterval(() => {
            commit(Mutations.updateTime)
        }, Const.updateNowInterval)
    }
}