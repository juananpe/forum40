<template>
  <div>
    <v-app-bar flat color="indigo" max-height="60" dark>
      <v-toolbar-title>Forum 4.0 – Analyse von Online-Nutzerkommentaren</v-toolbar-title>
      <v-spacer></v-spacer>
      <UserLogin />
    </v-app-bar>
  </div>
</template>

<script>
import UserLogin from "./UserLogin";
export default {
  data() {
    return {
      drawer: false,
      items: [
        { title: "Analyse", icon: "bar_chart" },
        { title: "Annotation", icon: "check" }
      ]
    };
  },
  components: {
    UserLogin
  }
};
</script>

<style>
</style>
