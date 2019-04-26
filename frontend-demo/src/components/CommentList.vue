<template>
  <div>
    <h3>Comment List</h3>
    <button v-on:click="fetchComments()">Load placeholder comments</button>
    <div v-for="comment in allComments" :key="comment.id" class="comment">
      Name: {{comment.name}}
      Email: {{comment.email}}
      Body: {{comment.body}}
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from "vuex";

export default {
  name: "CommentList",
  methods: {
    ...mapActions(["fetchComments"])
  },
  computed: mapGetters(["allComments"])
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.comment {
  padding: 20px;
  border: 1px solid #ddd;
}
</style>
