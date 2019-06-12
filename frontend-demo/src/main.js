import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css' // Ensure you are using css-loader
import App from './App.vue'
import store from './store'
import VueTruncate from 'vue-truncate-filter'

// REST Client
import axios from 'axios'
import VueAxios from 'vue-axios'

// ECharts
import ECharts from 'vue-echarts'

Vue.use(Vuetify)
Vue.use(VueAxios, axios)
Vue.use(VueTruncate)

Vue.component('v-chart', ECharts)

Vue.config.productionTip = false

new Vue({
  store,
  render: h => h(App),
}).$mount('#app')
