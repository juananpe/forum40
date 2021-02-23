<template>
	<v-dialog v-model="dialog">
		<template #activator="slotProps">
			<slot name="activator" v-bind="slotProps" />
		</template>

		<v-card class="pb-8">
			<v-card-title>Thread</v-card-title>
			<v-card elevation="4" class="mx-10 mt-3 py-10 px-6">
				<UserCommentThread :comment="comment" />
			</v-card>

			<v-card-title>Document</v-card-title>
			<v-card elevation="4" class="mx-10 mt-3 pt-10 px-6">
				<DocumentPosition :comment="comment" />
			</v-card>
		</v-card>
	</v-dialog>
</template>

<script>
import DocumentPosition from './DocumentPosition.vue'
import UserCommentThread from './UserCommentThread.vue'

export default {
	props: [
		'comment',
	],
  components: { UserCommentThread, DocumentPosition },
	data() {
		return {
			dialog: false,
		}
	}
}
</script>
