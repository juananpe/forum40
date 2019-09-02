<template>
  <v-app-bar color="indigo" max-height="60" dark>
    <v-toolbar-title>Analyse von Online-Nutzerkommentaren</v-toolbar-title>
    <v-spacer></v-spacer>
    <UserLogin />
  </v-app-bar>
</template>

<script>
import UserLogin from "./UserLogin";
export default {
  components: {
    UserLogin
  }
};
</script>

<style>
</style>
