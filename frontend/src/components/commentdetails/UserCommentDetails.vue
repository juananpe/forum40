<template>
  <v-card>
    <v-tabs v-model="tab">
      <v-tab>{{ $t('comment_details.thread') }}</v-tab>
      <v-tab>{{ $t('comment_details.document') }}</v-tab>
      <v-tab>{{ $t('comment_details.similar') }}</v-tab>
    </v-tabs>

    <v-tabs-items v-model="tab">
      <v-tab-item>
        <UserCommentThread :comment="comment" class="tab-content"/>
      </v-tab-item>
      <v-tab-item>
        <DocumentPosition :comment="comment" class="tab-content" />
      </v-tab-item>
      <v-tab-item>
        <SimilarComments :comment="comment" class="tab-content" />
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
import UserCommentThread from './UserCommentThread';
import DocumentPosition from './DocumentPosition';
import SimilarComments from './SimilarComments';

export default {
  props: ['comment'],
  components: {
    UserCommentThread,
    DocumentPosition,
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
  .tab-content {
    padding: 1.6rem 2.5rem 1.3rem;
  }
</style>