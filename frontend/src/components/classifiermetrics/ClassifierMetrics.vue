<template>
	<div>
		<h3>{{ $t("classifier_metrics.title" ) }}</h3>

		<v-data-table
				:headers="headers"
				:items="labels"
				:loading="loading"
				item-key="label"
				:disable-sort="true"
				:hide-default-footer="true"
		>
			<template v-slot:item.lastUpdated="{ item }">
				<span v-if="item.lastUpdated === null" class="not-available">{{ $t("classifier_metrics.last_updated.never" ) }}</span>
				<span v-else>{{item.lastUpdated}}</span>
			</template>

			<template v-slot:item.accuracy="{ item }">
				<span v-if="item.accuracy === null" class="not-available">{{ $t("classifier_metrics.not_available" ) }}</span>
				<div v-else>
					<ScoreBar :value="item.accuracy" class="score-bar" />
					{{formatPercent(item.accuracy)}}
				</div>
			</template>

			<template v-slot:item.f1="{ item }">
				<span v-if="item.f1 === null" class="not-available">{{ $t("classifier_metrics.not_available" ) }}</span>
				<div v-else>
					<MinimalLineChart :values="item.f1" class="chart" />
					{{formatPercent(item.f1[item.f1.length-1])}}
				</div>
			</template>
		</v-data-table>
	</div>
</template>

<script>
	import Vue from "vue";
	import {mapGetters} from "vuex";
	import {Getters} from "../../store/const";
	import Service from "../../api/db";
	import moment from "moment";
	import MinimalLineChart from "./MinimalLineChart";
	import ScoreBar from "./ScoreBar";

	export default {
		name: "ClassifierMetrics",
		components: {
			ScoreBar,
			MinimalLineChart,
		},
		data() {
			return {
				labelModels: {},
				loading: false,
			}
		},
		computed: {
			...mapGetters([Getters.selectedLabels, Getters.getLabelIdByName]),
      headers() {
        return [
          { value: "labelName", text: this.$i18n.t("classifier_metrics.headers.label") },
          { value: "lastUpdated", text: this.$i18n.t("classifier_metrics.headers.last_updated") },
          { value: "accuracy", text: this.$i18n.t("classifier_metrics.headers.accuracy") },
          { value: "f1", text: this.$i18n.t("classifier_metrics.headers.f1") },
        ]
      },
			labels() {
				return this[Getters.selectedLabels]
					.map((labelName) => [labelName, this[Getters.getLabelIdByName](labelName)])
					.filter(([, labelId]) => this.labelModels.hasOwnProperty(labelId))
					.map(([labelName, labelId]) => {
						const models = this.labelModels[labelId];

						if (models.length >= 1) {
							return {
								labelName,
								lastUpdated: moment.max(models.map(model => moment(model["timestamp"]))).format("DD.MM.YYYY"),
								accuracy: models[models.length-1]["acc"],
								f1: models.map(model => model["f1"]),
							}
						} else {
							return {
								labelName,
								lastUpdated: null,
								accuracy: null,
								f1: null,
							}
						}
					})
			},
		},
		watch: {
			[Getters.selectedLabels]: function (val) {
				Object.values(val)
					.map(this[Getters.getLabelIdByName])
					.filter((labelId) => !this.labelModels.hasOwnProperty(labelId))
					.map(this.fetchLabelModels);
			},
		},
		methods: {
			async fetchLabelModels(labelId) {
				const { data } = await Service.getModels(labelId);
				Vue.set(this.labelModels, labelId, data);
			},
			formatPercent(v) {
				return (v*100).toFixed(0) + "%";
			}
		}
	}
</script>

<style scoped>
	.not-available {
		color: #aaa;
	}

	.chart, .score-bar {
		display: inline-block;
		width: 6em;

		vertical-align: middle;
		margin-right: 0.4rem;
	}

	.chart {
		height: 1.3em;
	}

	.score-bar {
		height: 1em;
	}
</style>
