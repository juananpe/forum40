<template>
  <div>
    <!-- <h3>Aktive Filter</h3>
    <v-layout wrap>
      <v-flex xs12>
        <v-chip v-for="filter in _activeFilters" v-bind:key="filter">{{filter}}</v-chip>
      </v-flex>
    </v-layout> -->
    
    <v-layout>
      <v-flex xs12>
        <DataSelector/>
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import DataSelector from "./DataSelector";
import { Getters } from "../store/const";
import { mapGetters } from "vuex";
export default {
  data() {
    return {};
  },
  computed: {
    ...mapGetters([Getters.activeFilters]),
    _activeFilters() {
      return this.activeFilters;
    }
  },

  methods: {},
  components: {
    DataSelector
  }
};
</script>

<style>
</style>
