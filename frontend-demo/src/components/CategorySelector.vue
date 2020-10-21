<template>
  <v-autocomplete
    v-if="showComponent()"
    :items="categories"
    :label="$t('category.menue')"
    @change="valueChanged"
    dense
  ></v-autocomplete>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { State, Getters, Mutations } from "../store/const";
import { mapState, mapGetters, mapMutations } from "vuex";

export default {
  name: "CategorySelector",
  data() {
    return {
      categories: [],
    };
  },
  mounted() {},
  methods: {
    ...mapMutations([Mutations.setCategory]),
    valueChanged(value) {
      this[Mutations.setCategory](value);
    },
    showComponent() {
      return this.selectedSource === "SPIEGEL Online";
    },
    fetchCategories(newSelectedId) {
      Service.get(Endpoint.CATEGORIES(newSelectedId)).then(({ data }) => {
        this.categories = data;
      });
    },
  },
  watch: {
    [Getters.getSelectedSource](newSelectedSource) {
      if (this.showComponent()) {
        this.fetchCategories(newSelectedSource.id);
      } else {
          this[Mutations.setCategory]("");
      }
    },
  },
  computed: {
    ...mapState([State.source, State.selectedCategory]),
    ...mapGetters([Getters.getSelectedSource]),
    selectedSource() {
      return this[State.source];
    },
  },
};
</script>

<style>
</style>