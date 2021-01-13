<template>
	<v-chart :options="chartOptions" :autoresize="true" />
</template>

<script>
	import ECharts from "vue-echarts";
	import "echarts/lib/chart/line";

	export default {
		name: "MinimalLineChart",
		components: {
			"v-chart": ECharts,
		},
		props: [ "values" ],
		data() {
			return {
				chartOptions: {
					animation: false,
					grid: {
						left: 3,
						right: 3,
						top: 3,
						bottom: 3,
					},
					xAxis: {
						type: "category",
						show: false,
						boundaryGap: false,
					},
					yAxis: {
						type: "value",
						show: false,
						min: "dataMin",
						max: "dataMax",
					},
					series: [{
						type: "line",
						data: this.values,
						smooth: true,
						animation: false,
						cursor: "unset",
						itemStyle: {
							color: "black",
						}
					}]
				},
			}
		}
	}
</script>

<style scoped>

</style>
