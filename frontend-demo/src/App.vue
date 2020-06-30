<template>
  <v-app>
    <TopToolbar />
    <v-container>
      <v-layout wrap>
        <v-flex xs12>
          <UserCommentFilter />
        </v-flex>
        <v-flex xs12 class="pb-4"></v-flex>
        <h3>Kommentaraufkommen im zeitlichen Verlauf</h3>
        <v-flex class="text-xs-center" xs12>
          <TimefrequenzRadioGroup />
        </v-flex>
        <v-flex xs12>
          <TimeChart />
        </v-flex>
        <v-flex xs12 class="pb-4"></v-flex>
        <v-flex xs12>
          <ClassifierMetrics />
        </v-flex>
        <v-flex xs12 class="pb-4"></v-flex>
        <v-flex xs12>
          <UserCommentList />
        </v-flex>
        <v-flex xs12 class="pb-4"></v-flex>
        <v-flex xs12>
          <UserCommentThread />
        </v-flex>
      </v-layout>
    </v-container>
  </v-app>
</template>

<script>
import TopToolbar from "./components/TopToolbar";
import TimeChart from "./components/TimeChart";
import TimefrequenzRadioGroup from "./components/TimefrequenzRadioGroup";
import UserCommentList from "./components/UserCommentList";
import UserCommentFilter from "./components/UserCommentFilter";
import UserCommentThread from "./components/UserCommentThread";
import { mapActions } from "vuex";
import ClassifierMetrics from "./components/classifiermetrics/ClassifierMetrics";

export default {
  name: "App",
  components: {
    ClassifierMetrics,
    TopToolbar,
    TimeChart,
    TimefrequenzRadioGroup,
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
