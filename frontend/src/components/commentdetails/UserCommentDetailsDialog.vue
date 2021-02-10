<template>
	<v-dialog v-model="dialog">
		<template #activator="slotProps">
			<slot name="activator" v-bind="slotProps" />
		</template>

		<v-card>
			<v-card-title>Comment Details</v-card-title>

			<UserCommentThread :comment="comment" />
			<DocumentPosition :comment="comment" />
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