<template>
  <div>
    <v-layout>
      <v-flex xs12>
        <v-autocomplete
          :items="categories"
          v-model="value"
          :label="$t('category.menue')"
          dense
        ></v-autocomplete>
      </v-flex>
    </v-layout>
    <v-layout>
      <v-flex xs12>
        <v-chart :options="pie" :autoresize="true" @click="chartClicked" />
      </v-flex>
    </v-layout>
  </div>
</template>

<script>
import Service, { Endpoint } from "../api/db";
import { State, Getters, Mutations } from "../store/const";
import { mapState, mapGetters, mapMutations } from "vuex";
import ECharts from "vue-echarts";
import "echarts/lib/chart/pie";
import "echarts/lib/component/tooltip";

export default {
  name: "CategorySelector",
  data() {
    return {
      categories: [],
      pie: {
        series: [
          {
            type: "pie",
            data: [],
            radius: '60%',
            label: {
              show: false,
              margin: 200,
              alignTo: 'edge',
              normal: {
                formatter: "{b}\n({c})",
                position: "outside",
              },
            },
          },
        ],
      },
    };
  },
  mounted() {},
  methods: {
    ...mapMutations([Mutations.setCategory]),
    valueChanged(value) {
      this[Mutations.setCategory](value);
    },
    fetchCategories(newSelectedId) {
      Service.get(Endpoint.CATEGORIES(newSelectedId)).then(({ data }) => {
        this.categories = data.names;
        this.pie.series[0].data = data.data.sort((a, b) => a.value > b.value);
      });
    },
    chartClicked(event) {
      this.valueChanged(event.name);
    }
  },
  watch: {
    [Getters.getSelectedSource](newSelectedSource) {
      if (newSelectedSource) {
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
    value: {
      get() {
        return this[State.selectedCategory];
      },
      set(value) {
        this.valueChanged(value)
      }
    }
  },
  components: {
    "v-chart": ECharts,
  },
};
</script>

<style scoped>
</style>