<template>
  <div id="app">
    <v-app>
      <TopToolbar/>
      <v-container>
        <v-layout row wrap>
          <v-flex xs12>
            <UserCommentFilter/>
          </v-flex>
          <v-flex xs12>
            <TimeChart/>
            <TimeChart_E/>
          </v-flex>
          <v-flex xs12>
            <UserCommentList/>
          </v-flex>
          <v-flex xs12>
            <UserCommentThread/>
          </v-flex>
        </v-layout>
      </v-container>
    </v-app>
  </div>
</template>

<script>
import TopToolbar from "./components/TopToolbar";
import TimeChart from "./components/TimeChart";
import TimeChart_E from "./components/TimeChart_E";
import UserCommentList from "./components/UserCommentList";
import UserCommentFilter from "./components/UserCommentFilter";
import UserCommentThread from "./components/UserCommentThread";
import { mapActions } from "vuex";

export default {
  name: "app",
  components: {
    TopToolbar,
    TimeChart,
    TimeChart_E,
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
</style>
