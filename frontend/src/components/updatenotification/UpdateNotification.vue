<template>
  <div v-if="labelStates.length > 0" class="scroll-spacer">
    <div class="container">
      <div v-for="state in labelStates" :key="state['id']" class="label-status">
        <div class="label-header">
          <h3 class="label-name">{{state['labelName']}}</h3>
          <span :class="['status-badge', state['status']]">{{state['status']}}</span>
        </div>
        <CompositeProgress :steps="state['steps']"/>
      </div>
    </div>
  </div>
</template>

<script>
import CompositeProgress from "@/components/updatenotification/CompositeProgress";
import {mapGetters} from "vuex";
import {Getters} from "@/store/const";

export default {
  name: "UpdateNotification",
  components: {CompositeProgress},
  data() {
    return {
      latestUpdateByLabelId: {},
    }
  },
  computed: {
    ...mapGetters([Getters.selectedLabels, Getters.getLabelIdByName]),
    labelStates() {
      return this[Getters.selectedLabels]
          .map((labelName) => {
            const labelId = this[Getters.getLabelIdByName](labelName);
            const latestUpdate = this.latestUpdateByLabelId[labelId];
            if (latestUpdate === undefined) {
              return null;
            }

            const currentlyTraining = latestUpdate['name'] === 'classification_train';
            const trainProgress = currentlyTraining ? this.getTrainProgress(latestUpdate) : 1;
            const updateProgress = currentlyTraining ? 0 : this.getUpdateProgress(latestUpdate);
            const finished = updateProgress === 1;
            if (finished) {
              setTimeout(() => {
                if (this.latestUpdateByLabelId[labelId] === latestUpdate) {
                  this.$delete(this.latestUpdateByLabelId, labelId);
                }
              }, 5000);
            }

            return {
              labelId,
              labelName,
              status: finished ? 'finished' : 'processing',
              steps: [
                {name: 'Training', weight: 1, progress: trainProgress},
                {name: 'Updating', weight: 3, progress: updateProgress},
              ]
            }
          }).filter(step => step !== null);
    }
  },
  methods: {
    getTrainProgress(update) {
      const {data: {status, step, progress}} = update;
      if (status === 'starting') return 0/4;
      if (step === 'hyperparam') return 0/4 + 1/4 * (progress['current'] / progress['total']);
      if (step === 'train') return 2/4;
      if (step === 'cv') return 3/4;
      if (status === 'finished' || status === 'failed') return 4/4;
      throw Error(`Unknown training update received: ${JSON.stringify(update)}`);
    },
    getUpdateProgress(update) {
      const {data: {status, progress}} = update;
      if (status === 'starting') return 0;
      if (status === 'finished' || status === 'failed') return 1;
      return 9/10 * (progress['current'] / progress['total']);  // batch processing takes approx. 9/10 of the update time
    },
  },
  sockets: {
    task_update(payload) {
      const {name, data: {label_id: labelId}} = payload;
      const isClassificationUpdate = ['classification_update', 'classification_train'].includes(name);
      if (isClassificationUpdate && labelId) {
        this.$set(this.latestUpdateByLabelId, labelId, payload);
      }
    },
  },
}
</script>

<style scoped>
.scroll-spacer {
  height: 8rem;
}

.container {
  z-index: 100;
  position: fixed;
  bottom: 0;
  right: 4rem;
  width: 25rem;
  background-color: white;
  border-radius: 0.3rem 0.3rem 0 0;
  box-shadow: 0 4px 17px 0 rgba(0, 0, 0, 0.2), 0 2px 5px 0 rgba(0, 0, 0, 0.4);
  padding: 0.7rem 1.9rem 1.8rem;
}

.label-header {
  margin: 0.4rem 0;
  display: flex;
  align-items: center;
}

.label-name {
  display: inline-block;
}

.status-badge {
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
  padding: 0.15rem 0.6rem;
  margin-left: 1rem;
  border-radius: 0.3rem;
}

.status-badge.processing {
  background-color: #E3BE3C;
}

.status-badge.finished {
  background-color: #5EB141;
}
</style>
