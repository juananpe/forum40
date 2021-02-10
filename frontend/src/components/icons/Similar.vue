<template>
	<img :src="icon" class="icon" />
</template>

<script>
export default {
	data() {
		return {
			icon: require('../../assets/icons/similar.svg'),
		}
	}
}
</script>

<style>
.icon {
	height: 24px;
}
</style>
