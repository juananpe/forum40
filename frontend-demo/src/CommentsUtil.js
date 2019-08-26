export const getLabels = (comment, labelId) => {
    const labels = comment.labels;
    return labels.filter(label => label.labelId.$oid === labelId);
}