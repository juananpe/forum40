<template>
  <td colspan="100%" class="elevation-1">
    <v-btn
      v-if="!similar_texts.length"
      outlined
      small
      color="primary"
      text
      @click="loadSimilarComments()"
    >Ähnliche Kommentare anzeigen</v-btn>

    <v-container fluid>
      <v-row dense>
        <v-card
          v-for="(comment, i) in similar_texts.slice(0,MAX_COMMENTS)"
          :key="i"
          max-width="'100%'"
          outlined
        >
          <v-list-item three-line>
            <v-list-item-content>{{i+1}}. {{comment}}</v-list-item-content>
          </v-list-item>
        </v-card>
      </v-row>
    </v-container>
  </td>
</template>
  

<script>
import Service, { Endpoint } from "../api/db";

export default {
  props: {
    comment: Object
  },
  data() {
    return {
      similar_texts: [],
      MAX_COMMENTS: 3
    };
  },
  methods: {
    async loadSimilarComments() {
      const payload = {
        comments: [this.comment.text],
        n: 3
      };
      try {
        const { data } = await Service.post(Endpoint.COMMENTS_SIMILAR, payload);
        this.similar_texts = data[0];
        console.log(data[0]);
      } catch (e) {
        console.error("Could not load similar comments!");
      }
    }
  }
};
</script>

<style>
</style>