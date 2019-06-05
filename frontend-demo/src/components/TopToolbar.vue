<template>
  <v-toolbar color="indigo" dark>
    <v-toolbar-title>Nutzerkommentare</v-toolbar-title>
    <v-spacer></v-spacer>
    <LabelEditor/>
    <UserLogin/>
  </v-toolbar>
</template>

<script>
import UserLogin from "./UserLogin";
import LabelEditor from "./LabelEditor";
export default {
  components: {
    UserLogin,
    LabelEditor
  }
};
</script>

<style>
</style>
