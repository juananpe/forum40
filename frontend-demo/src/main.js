import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'

import store from './store'
import VueTruncate from 'vue-truncate-filter'

// REST Client
import axios from 'axios'
import VueAxios from 'vue-axios'

// ECharts
import ECharts from 'vue-echarts'

Vue.use(VueAxios, axios)
Vue.use(VueTruncate)

Vue.component('v-chart', ECharts)

Vue.config.productionTip = false

new Vue({
  vuetify,
  store,
  render: h => h(App),
}).$mount('#app')
