<template>
  <td colspan="100%" class="elevation-1">
    <v-btn
      outlined
      small
      color="primary"
      text
      @click="loadSimilarComments()"
    >Ähnliche Kommentare anzeigen</v-btn>
  </td>
</template>
  

<script>
import Service, { Endpoint } from "../api/db";

export default {
  props: {
    comment: Object
  },

  methods: {
    async loadSimilarComments() {
      const payload = {
        comments: [this.comment.text],
        n: 10
      };
      try {
        const { data } = await Service.post(Endpoint.COMMENTS_SIMILAR, payload);
        console.log(data);
      } catch (e) {
        console.error("Could not load similar comments!");
      }
    }
  }
};
</script>

<style>
</style>