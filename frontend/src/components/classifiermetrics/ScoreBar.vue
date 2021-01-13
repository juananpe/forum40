<template>
	<div class="outer">
		<div
				class="inner"
				:style="{'background-color': fillColor, 'width': width}"
		/>
	</div>
</template>

<script>
	export default {
		name: "ScoreBar",
		props: ["value"],
		data() {
			// fill steps generated using chroma.js:
			// chroma.scale(["#E1725A","#EFBA32","#E9DF00","#85D95E"]).domain([0.3, 0.7, 0.8, 1]).mode("lch").colors(10)
			return {
				fillSteps: ["#e1725a","#e97e52","#ef8b4a","#f29942","#f2a83a","#f0b833","#edd218","#d1df22","#aadd43","#85d95e"],
			}
		},
		computed: {
			fillColor() {
				const fillIndex = Math.min(this.fillSteps.length-1, Math.floor(this.value * this.fillSteps.length))
				return this.fillSteps[fillIndex];
			},
			width() {
				return `${this.value*100}%`;
			}
		}
	}
</script>

<style scoped>
	.outer {
		background-color: #e7e7e7;
	}

	.inner {
		height: 100%;
	}

	.outer, .inner {
		border-radius: 0.3rem;
	}
</style>
