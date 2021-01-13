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
    <v-layout>
      <v-flex xs5>
        <CategorySelector/>
      </v-flex>
      <v-flex xs7>
        <h3>{{ $t("time_chart.title") }}</h3>
        <TimefrequenzRadioGroup />
        <TimeChart />
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import DataSelector from "./DataSelector";
import TimeChart from "./TimeChart"
import TimefrequenzRadioGroup from "./TimefrequenzRadioGroup"
import CategorySelector from "./CategorySelector";
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
    DataSelector,
    CategorySelector,
    TimeChart,
    TimefrequenzRadioGroup
  }
};
</script>

<style>
</style>
