from BertFeatureExtractor import BertFeatureExtractor
import logging
import torch

logger = logging.getLogger()

logger.info('Loading BERT model')
be = BertFeatureExtractor(
    batch_size=8,
    device='cuda' if torch.cuda.is_available() else 'cpu',
    keep_cls=False,
    use_layers=4,
    use_token=True
)
logger.info('BERT model loaded')


def get_embeddings(sequences):
    return be.extract_features(sequences)
