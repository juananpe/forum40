import Vue from "vue";
import VueI18n from "vue-i18n";
import de from './locales/de.json';

Vue.use(VueI18n);

const messages = { de };

export default new VueI18n({
	locale: process.env.VUE_APP_LOCALE,
	messages,
})
