export const State = {
    labels: 'labels',
    source: 'source',
    sources: 'sources',
    selectedFilters: 'selectedFilters',
    selectedViewAggregations: 'selectedViewAggregations',
    selectedLabels: 'selectedLabels',
    timeFrequency: 'timeFrequency',
    keywordfilter: 'keywordfilter',
    currentJWT: 'currentJWT',
    now: 'now',
    refreshTokenInterval: 'refreshTokenInterval',
    selectedCategory: 'selectedCategory'
}

export const Getters = {
    jwt: 'jwt',
    jwtData: 'jwtData',
    jwtUser: 'jwtUser',
    jwtExpiration: 'jwtExpiration',
    jwtLoggedIn: 'jwtLoggedIn',
    labelParameters: 'labelParameters',
    selectedLabels: 'selectedLabels',
    keywordfilter: 'keywordfilter',
    activeFilters: 'activeFilters',
    timeFrequency: 'timeFrequency',
    getSelectedSource: 'getSelectedSource',
    getLabelname: 'getLabelname',
    getLabelIdByName: 'getLabelIdByName'
}

export const Mutations = {
    setSelectedLabels: "setSelectedLabels",
    setJWT: "setJWT",
    updateTime: "updateTime",
    setKeywordfilter: "setKeywordfilter",
    setTimeFrequency: "setTimeFrequency",
    setLabels: "setLabels",
    setSource: "setSource",
    setSources: "setSources",
    setCategory: "setCategory",
}

export const Actions = {
    login: 'login',
    logout: 'logout',
    refreshToken: 'refreshToken',
    start: 'start'
}
