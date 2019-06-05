<template>
  <div id="app">
    <v-app>
      <TopToolbar/>
      <v-layout row wrap>
        <v-flex xs12 md10 offset-md1 mt-3>
          <UserCommentFilter/>
        </v-flex>

        <v-flex xs12 md10 offset-md1>
          <TimeChart/>
        </v-flex>
        <v-flex xs12 md10 offset-md1>
          <UserCommentList/>
        </v-flex>
        <v-flex xs12 md10 offset-md1>
          <UserCommentThread/>
        </v-flex>
      </v-layout>
    </v-app>
  </div>
</template>

<script>
import TopToolbar from "./components/TopToolbar";
import TimeChart from "./components/TimeChart";
import UserCommentList from "./components/UserCommentList";
import UserCommentFilter from "./components/UserCommentFilter";
import UserCommentThread from "./components/UserCommentThread";
import { mapActions } from "vuex";

export default {
  name: "app",
  components: {
    TopToolbar,
    TimeChart,
    UserCommentList,
    UserCommentFilter,
    UserCommentThread
  },
  methods: {
    ...mapActions(["start"])
  },
  created() {
    this.start();
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
