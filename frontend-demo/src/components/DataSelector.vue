<template>
  <v-combobox v-model="selection" :items="items" label="Label" chips clearable multiple>
    <template v-slot:selection="data">
      <v-chip :selected="data.selected" close @input="remove(data.item)">
        <strong>{{ data.item }}</strong>
      </v-chip>
    </template>
  </v-combobox>
</template>

<script>
import { State, Mutations } from "../store/const";
import { mapState, mapMutations } from "vuex";
import Service from "../api/db";

export default {
  name: "DataSelector",
  data: () => ({
    items: []
  }),
  methods: {
    ...mapMutations([Mutations.setSelectedLabels]),
    async fetchLabels() {
      const { data } = await Service.get("db/labels/");
      this.items = data.labels;
    },
    remove(item) {
      this.selection.splice(this.selection.indexOf(item), 1);
      this.selection = [...this.selection];
    }
  },
  mounted() {
    this.fetchLabels();
  },
  computed: {
    ...mapState([State.selectedLabels]),
    selection: {
      set(state) {
        this.setSelectedLabels(state);
      },
      get() {
        return this.selectedLabels;
      }
    }
  }
};
</script>

<style>
</style>
