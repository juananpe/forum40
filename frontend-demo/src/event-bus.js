import Vue from 'vue';
export const EventBus = new Vue();

export const Events = {
    loggedIn: 'loggedIn',
    sourceLoaded: 'sourceLoaded'
}