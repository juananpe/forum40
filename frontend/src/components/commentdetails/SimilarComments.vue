<template>
  <v-progress-circular v-if="similarComments === null" :indeterminate="true" />

  <div v-else class="comment-list">
    <UserComment 
      v-for="similarComment of similarComments"
      :key="similarComment.id"
      :comment="similarComment"
    />
  </div>
</template>

<script>
import Service from "../../api/db";
import UserComment from './UserComment';

export default {
  components: {
    UserComment,
  },
  props: ['comment'],
  data() {
    return {
      similarComments: null,
    }
  },
  watch: {
    comment: {
      immediate: true,
      async handler(comment) {
        this.similarComments = null;
        const { data } = await Service.getSimilarComments(comment.id);
        this.similarComments = data;
      },
    },
  },
}
</script>

<style scoped>
  .comment-list > *:not(:first-child) {
    margin-top: 1rem;
  }
</style>
