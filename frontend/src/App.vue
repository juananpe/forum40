<template>
  <v-app>
    <TopToolbar />
    <v-container>
      <v-layout wrap>
        <v-flex xs12>
          <UserCommentFilter />
        </v-flex>
        <v-flex xs12>
          <ClassifierMetrics />
        </v-flex>
        <v-flex xs12>
          <UserCommentList />
        </v-flex>
      </v-layout>
      <UpdateNotification />
    </v-container>
  </v-app>
</template>

<script>
import TopToolbar from "./components/TopToolbar";
import UserCommentList from "./components/UserCommentList";
import UserCommentFilter from "./components/UserCommentFilter";
import { mapActions } from "vuex";
import ClassifierMetrics from "./components/classifiermetrics/ClassifierMetrics";
import UpdateNotification from "@/components/updatenotification/UpdateNotification";

export default {
  name: "App",
  components: {
    UpdateNotification,
    ClassifierMetrics,
    TopToolbar,
    UserCommentList,
    UserCommentFilter,
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
