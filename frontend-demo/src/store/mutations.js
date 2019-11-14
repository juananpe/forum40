import { State, Mutations } from './const'
import { EventBus, Events } from "../event-bus";

export default {
    [Mutations.setJWT]: (state, jwt) => (state[State.currentJWT] = jwt),
    [Mutations.updateTime]: (state) => (state[State.now] = new Date()),
    [Mutations.setSelectedComment]: (state, comment) => (state[State.selectedComment] = comment),
    [Mutations.setSelectedLabels]: (state, selection) => (state[State.selectedFilters][State.selectedLabels] = selection),
    [Mutations.setKeywordfilter]: (state, keyword) => (state[State.selectedFilters][State.keywordfilter] = keyword),
    [Mutations.setTimeFrequency]: (state, mode) => (state[State.selectedViewAggregations][State.timeFrequency] = mode),
    [Mutations.setLabels]: (state, labels) => (state[State.labels] = labels),
    [Mutations.setSource]: (state, source) => {
        state[State.source] = source;
        EventBus.$emit(Events.sourceLoaded);
    },
    [Mutations.setSources]: (state, sources) => (state[State.sources] = sources),
}