<template>
  <v-toolbar color="indigo" dark>
    <v-toolbar-title>Nutzerkommentare</v-toolbar-title>
    <v-spacer></v-spacer>
    <UserLogin/>
  </v-toolbar>
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
