export const State = {
    selectedFilters: 'selectedFilters',
    selectedLabels: 'selectedLabels',
    keywordfilter: 'keywordfilter',
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
    selectedCommentId: 'selectedCommentId',
    selectedLabels: 'selectedLabels',
    keywordfilter: 'keywordfilter'
}

export const Mutations = {
    setSelectedLabels: "setSelectedLabels",
    setJWT: "setJWT",
    updateTime: "updateTime",
    setSelectedComment: "setSelectedComment",
    setKeywordfilter: "setKeywordfilter" 
}

export const Actions = {
    login: 'login',
    refreshToken: 'refreshToken',
    logout: 'logout',
    start: 'start'
}