<template>
  <v-combobox v-model="selection" :items="items" label="Label-Filter" chips clearable multiple>
    <template v-slot:selection="data">
      <v-chip :selected="data.selected" close @input="remove(data.item)">
        <strong>{{ data.item }}</strong>
      </v-chip>
    </template>
  </v-combobox>
</template>

<script>
import { Getters, Mutations } from "../store/const";
import { mapGetters, mapMutations } from "vuex";
import Service, { Endpoint } from "../api/db";

export default {
  name: "DataSelector",
  data: () => ({
    items: []
  }),
  methods: {
    ...mapMutations([Mutations.setSelectedLabels]),
    async fetchLabels() {
      const { data } = await Service.get(Endpoint.LABELS);
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
    ...mapGetters([Getters.selectedLabels]),
    selection: {
      set(state) {
        this[Mutations.setSelectedLabels](state);
      },
      get() {
        return this[Getters.selectedLabels];
      }
    }
  }
};
</script>

<style>
</style>
