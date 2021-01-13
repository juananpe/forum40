<template>
  <div class="label-status-progress">
    <div v-for="step of steps" :key="step['name']" class="step" :style="{flex: step['weight']}">
      <span class="step-name">{{step['name']}}</span>
      <div class="bar">
        <div class="bar-fill" :style="{width: `${step['progress']*100}%`}"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CompositeProgress",
  props: ['steps'],
}
</script>

<style scoped>
.label-status-progress {
  display: flex;
}

.step:not(:first-child) {
  margin-left: 1rem;
}

.bar {
  height: 0.8rem;
  background-color: #F0F0F0;
  margin-top: 0.2rem;
  border-radius: 0.3rem;
  overflow: hidden;
}

.bar-fill {
  background-color: #5EB141;
  height: 100%;
  border-radius: inherit;
  transition: width 1s ease;
}

.step-name {
  font-size: 0.9rem;
  color: #757575;
}
</style>
