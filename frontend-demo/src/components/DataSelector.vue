<template>
  <v-select :items="items" v-model="selection" label="Label" class="select"></v-select>
</template>

<script>
import { mapState, mapMutations } from "vuex";
import Service from "../api/db";

export default {
  name: "DataSelector",
  data: () => ({
    // TODO DB query
     items: []
  }),
  methods: {
    ...mapMutations(["setCurrentLabel"]),
    async loadData() {
      this.fetchLabels()
    },
    async fetchLabels() {
      const { data }  = await Service.get('db/labels/')
      this.items = data.labels
    }
  },
  mounted() {
    this.loadData()
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
  padding-top: 22px;
}
</style>
