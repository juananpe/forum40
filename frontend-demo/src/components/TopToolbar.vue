<template>
  <div>
    <v-app-bar flat color="indigo" max-height="60" dark>
      <v-toolbar-title>{{ $t("top_toolbar.title") }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <LanguageSelect class="mr-2" />
      <UserLogin />
    </v-app-bar>
  </div>
</template>

<script>
import UserLogin from "./UserLogin";
import LanguageSelect from "@/components/LanguageSelect";
export default {
  data() {
    return {
      drawer: false,
      items: [
        { title: this.$i18n.t('top_toolbar.analysis'), icon: "bar_chart" }, // TODO: Check if needed?
        { title: this.$i18n.t('top_toolbar.annotation'), icon: "check" }
      ]
    };
  },
  components: {
    LanguageSelect,
    UserLogin
  }
};
</script>

<style>
</style>
