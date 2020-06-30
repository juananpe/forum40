export const State = {
    labels: 'labels',
    source: 'source',
    sources: 'sources',
    selectedFilters: 'selectedFilters',
    selectedViewAggregations: 'selectedViewAggregations',
    selectedLabels: 'selectedLabels',
    timeFrequency: 'timeFrequency',
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
    keywordfilter: 'keywordfilter',
    activeFilters: 'activeFilters',
    timeFrequency: 'timeFrequency',
    getSelectedSource: 'getSelectedSource',
    getLabelname: 'getLabelname',
    getLabelIdByName: 'getLabelIdByName',
}

export const Mutations = {
    setSelectedLabels: "setSelectedLabels",
    setJWT: "setJWT",
    updateTime: "updateTime",
    setSelectedComment: "setSelectedComment",
    setKeywordfilter: "setKeywordfilter",
    setTimeFrequency: "setTimeFrequency",
    setLabels: "setLabels",
    setSource: "setSource",
    setSources: "setSources"
}

export const Actions = {
    login: 'login',
    logout: 'logout',
    refreshToken: 'refreshToken',
    start: 'start'
}
