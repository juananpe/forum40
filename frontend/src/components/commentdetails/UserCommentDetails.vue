<template>
  <v-card>
    <v-tabs v-model="tab">
      <v-tab>{{ $t('comment_details.thread') }}</v-tab>
      <v-tab>{{ $t('comment_details.similar') }}</v-tab>
    </v-tabs>

    <v-tabs-items v-model="tab">
      <v-tab-item>
        <UserCommentThread :comment="comment" />
      </v-tab-item>
      <v-tab-item>
        <SimilarComments :comment="comment" />
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
import UserCommentThread from './UserCommentThread';
import SimilarComments from './SimilarComments';

export default {
  props: ['comment'],
  components: {
    UserCommentThread,
    SimilarComments
  },
  data() {
    return {
      tab: 0,
    }
  },
}
</script>

<style scoped>

</style>