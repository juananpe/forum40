import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'

import store from './store'
import i18n from "./i18n";
import VueTruncate from 'vue-truncate-filter'
import VueSocketIO from "vue-socket.io";
import io from "socket.io-client";

// REST Client
import axios from 'axios'
import VueAxios from 'vue-axios'

// ECharts
import ECharts from 'vue-echarts'

Vue.use(VueAxios, axios)
Vue.use(VueTruncate)
Vue.use(new VueSocketIO({
  connection: io('https://localhost/', {path: '/api/socket.io'}),
}))

Vue.component('v-chart', ECharts)

Vue.config.productionTip = false

new Vue({
  vuetify,
  store,
  i18n,
  render: h => h(App),
}).$mount('#app')
