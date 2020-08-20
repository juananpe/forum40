import Vue from "vue";
import VueI18n from "vue-i18n";
import de from './locales/de.json';
import en from './locales/en.json';

Vue.use(VueI18n);

const messages = { de, en };

export default new VueI18n({
	locale: process.env.VUE_APP_LOCALE,
	messages,
})
