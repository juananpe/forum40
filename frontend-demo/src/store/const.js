export const State = {
    selectedLabels: 'selectedLabels',
    selectedComment: 'selectedComment',
    currentJWT: 'currentJWT',
    now: 'now',
    refreshTokenInterval: 'refreshTokenInterval'
}

export const Getters = {
    jwt: 'jwt',
    jwtData: 'jwtData',
    jwtUser: 'jwtUser',
    jwtExpiration: 'jwtExpiration',
    jwtLoggedIn: 'jwtLoggedIn',
    labelParameters: 'labelParameters',
    selectedCommentId: 'selectedCommentId'
}

export const Mutations = {
    setSelectedLabels: "setSelectedLabels",
    setJWT: "setJWT",
    updateTime: "updateTime",
    setSelectedComment: "setSelectedComment"
}

export const Actions = {
    login: 'login',
    refreshToken: 'refreshToken',
    logout: 'logout',
    start: 'start'
}