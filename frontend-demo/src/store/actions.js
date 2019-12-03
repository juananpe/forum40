import { Actions, Mutations } from './const'
import Const from '../const'
import Service, { Endpoint } from '../api/db'
import { EventBus, Events } from "../event-bus";

export default {
    [Actions.login]: async function ({ commit, getters, state, dispatch }, { username, password }) {
        try {
            const { data } = await Service.get(Endpoint.LOGIN(username, password));
            commit(Mutations.setJWT, data.token);
            state.refreshTokenInterval = setInterval(() => {
                if ((getters.jwtExpiration * 1000 - state.now) <= Const.refreshTokenBefore)
                    dispatch(Actions.refreshToken);
            }, Const.refreshTokenCheckInterval);
            EventBus.$emit(Events.loggedIn);

            return true;
        }
        catch (error) {
            return false;
        }
    },
    [Actions.logout]: function ({ commit }) {
        // TODO: Stop refresh token requests
        commit(Mutations.setJWT, '');
    },
    [Actions.refreshToken]: async function ({ commit, state }) {
        const { data } = await Service.get(Endpoint.REFRESH_TOKEN, state.currentJWT);
        if (data.token) {
            commit(Mutations.setJWT, data.token);
            return true;
        }
        return false;
    },
    [Actions.start]: function ({ commit }) {
        setInterval(() => {
            commit(Mutations.updateTime)
        }, Const.updateNowInterval)
    }
}