<template>
  <div>
    <b>{{title}}</b>
    <div>{{timestamp['$date']}}</div>
    <div>{{text}}</div>
    <button type="button" @click="annotated(true)">Yes</button>
    <button type="button" @click="annotated(false)">No</button>
  </div>
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
      let comment_id = this._id['$oid'];
      this.$emit("annotated", {comment_id, label});
    }
  }
};
</script>

<style>
</style>
