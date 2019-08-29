export const getLabels = (comment, labelId, username) => {

    const labels = comment.labels;
    if (labels) {
        const label = labels.find(label => label.labelId.$oid === labelId);
        if (label && label.manualLabels) {
            // only show annotation of username
            const manualLabel = label.manualLabels.find(ml => ml.annotatorId === username);
            if (manualLabel) {
                const filteredLabel = Object.assign({}, label);
                delete filteredLabel['manualLabels'];
                filteredLabel.manualLabel = manualLabel;
                filteredLabel.manualLabel.label = !!+manualLabel.label // convert str to bool
                return filteredLabel;
            }
            return label;
        }
    }
    return null;
}