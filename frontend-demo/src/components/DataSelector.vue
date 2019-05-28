<template>
    <v-select :items="items" v-model="selection" label="Label" class="select"></v-select>
</template>

<script>
import { mapState, mapMutations } from "vuex";

export default {
  name: "DataSelector",
  data: () => ({
    // TODO DB query
    items: [
      "argumentsused",
      "personalstories",
      "possiblyfeedback",
      "discriminating"
    ]
  }),
  methods: {
    ...mapMutations(["setCurrentLabel"])
  },
  computed: {
    ...mapState(["label"]),
    selection: {
      set(state) {
        this.setCurrentLabel(state);
      },
      get() {
        return this.label;
      }
    }
  }
};
</script>

<style>
.select {
  width: 50px;
  padding-left:20px;
  padding-top: 30px;
}
</style>
