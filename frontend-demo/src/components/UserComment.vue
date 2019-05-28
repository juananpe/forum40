<template>
  <v-card>
    <v-card-title primary-title>
      <div>
        <h3 class="headline mb-0">{{title}}</h3>
        <span>{{timestamp['$date']}}</span>
        <div>{{text}}</div>
      </div>
    </v-card-title>

    <v-card-actions>
      <v-btn flat color="blue" @click="annotated(true)">Ja</v-btn>
      <v-btn flat color="blue" @click="annotated(false)">Nein</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  name: "UserComment",
  props: {
    _id: Object,
    title: String,
    text: String,
    timestamp: Object
  },
  methods: {
    annotated: function(label) {
      let comment_id = this._id["$oid"];
      this.$emit("annotated", { comment_id, label });
    }
  }
};
</script>

<style>
</style>
