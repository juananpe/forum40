<template>
  <v-toolbar color="indigo" dark>
    <v-toolbar-title>Nutzerkommentare</v-toolbar-title>
    <DataSelector/>
    <v-spacer></v-spacer>
    <UserLogin/>
  </v-toolbar>
</template>

<script>
import DataSelector from "./DataSelector";
import UserLogin from "./UserLogin";
export default {
  components: {
    DataSelector,
    UserLogin
  }
};
</script>

<style>

</style>
