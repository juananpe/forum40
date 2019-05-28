<template>
  <div id="app">
    <TopToolbar/>
    <v-layout row wrap>
      <v-flex xs12 md8>
        <TimeChart/>
      </v-flex>
      <v-flex xs12 md4>
        <UserCommentList/>
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import TopToolbar from "./components/TopToolbar.vue";
import TimeChart from "./components/TimeChart.vue";
import UserCommentList from "./components/UserCommentList.vue";

export default {
  name: "app",
  components: {
    TopToolbar,
    TimeChart,
    UserCommentList
  }
};
</script>

<style>
#app {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
</style>
