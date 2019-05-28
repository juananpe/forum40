<template>
    <v-select :items="items" v-model="selection" label="Label" class="select"></v-select>
</template>

<script>
import { mapGetters, mapMutations } from "vuex";

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
    ...mapGetters(["currentLabel"]),
    selection: {
      set(state) {
        this.setCurrentLabel(state);
      },
      get() {
        return this.currentLabel;
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
