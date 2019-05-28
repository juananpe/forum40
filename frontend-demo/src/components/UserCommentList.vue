<template>
  <div>
    <h3>Kommentarliste</h3>

    <div class="container">
      <v-layout row wrap>
        <v-flex xs12 v-for="comment in comments" :key="comment.id">
          <user-comment v-bind="comment" @annotated="annotated"></user-comment>
        </v-flex>
      </v-layout>
    </div>
  </div>
</template>

<script>
import UserComment from "./UserComment";
import Service from "../api/db";
import { mapGetters, mapState } from "vuex";

export default {
  name: "UserCommentList",
  data() {
    return {
      comments: []
    };
  },
  computed: {
    ...mapState(['label'])
  },
  mounted() {
    this.fetchComments(this.label);
  },
  watch: {
    label(newLabel) {
      console.log(`Label changed to ${newLabel}`);
      this.fetchComments(newLabel);
    }
  },
  methods: {
    fetchComments(label) {
      Service.get("db/comments/" + label + "/0/10", (status, data) => {
        this.comments = data;
      });
    },

    annotated: function({ comment_id, label }) {
      console.log(`Annotated ${comment_id} with label ${label}`);
    }
  },
  components: {
    UserComment
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.container {
  display: flex;
  flex-wrap: wrap;
}
</style>
