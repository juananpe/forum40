export const getLabels = (comment, labelId) => {
    const labels = comment.labels;
    if (labels)
        return labels.filter(label => label.labelId.$oid === labelId);
    return []
}