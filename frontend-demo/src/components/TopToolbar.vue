<template>
  <v-toolbar color="indigo" dark>
    <v-toolbar-title>Nutzerkommentare</v-toolbar-title>
    <DataSelector/>
    <v-spacer></v-spacer>
    <v-btn flat>Login</v-btn>
  </v-toolbar>
</template>

<script>
import DataSelector from "./DataSelector";
export default {
  components: {
    DataSelector
  }
};
</script>

<style>

</style>
