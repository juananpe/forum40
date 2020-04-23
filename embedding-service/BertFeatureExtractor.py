# based on https://github.com/huggingface/pytorch-pretrained-BERT/blob/master/examples/extract_features.py
# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors and The HuggingFace Inc. team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Extract pre-computed feature vectors from a PyTorch BERT model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import re
import numpy as np

import torch
from torch.utils.data import TensorDataset, DataLoader, SequentialSampler

from pytorch_transformers import BertTokenizer
from pytorch_transformers import BertModel

logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = logging.ERROR)
logger = logging.getLogger(__name__)


class InputExample(object):

    def __init__(self, unique_id, text_a, text_b):
        self.unique_id = unique_id
        self.text_a = text_a
        self.text_b = text_b


class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, unique_id, tokens, input_ids, input_mask, input_type_ids):
        self.unique_id = unique_id
        self.tokens = tokens
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.input_type_ids = input_type_ids


class BertFeatureExtractor(object):

    def __init__(self, bert_model = "bert-base-german-cased", do_lower_case="False", max_seq_length=256,
                 batch_size=32, device = None,keep_cls=False, use_layers=4 , use_token=False):
        # parameter explanation
        # keep_cls is used to decide whether or not to keep CLS with all the tokens
        # use_layers is used to decide how many layers from the last layer to be used
        # use_token is used to decide whether to use the tokens or the CLS
        
        # number of layers cannot be greater than 13 (12 hidden +one output)
        if(use_layers > 13):
            use_layers=13


        if device:
            print("Configured device: " + device)
            self.device = torch.device(device)
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print("Selected device: " + device)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.n_gpu = torch.cuda.device_count()
        print("Device: {} n_gpu: {}".format(self.device, self.n_gpu))

        self.layer_weights = list(np.arange(1,use_layers+1))
        self.layer_indexes = [int(-x) for x in self.layer_weights]
        self.layer_weights.sort(reverse=True)
        self.keep_cls =keep_cls
        self.use_token= use_token

        # self.layers = "-1,-2,-3,-4"
        # self.layer_weights = [4, 3, 2, 1]
        # self.layer_indexes = [int(x) for x in self.layers.split(",")]

        self.bert_model = bert_model
        self.do_lower_case = do_lower_case
        self.max_seq_length = max_seq_length
        self.batch_size = batch_size

        self.tokenizer = BertTokenizer.from_pretrained(self.bert_model, do_lower_case=self.do_lower_case,
                                                       cache_dir="./model")

        self.model = BertModel.from_pretrained(self.bert_model, cache_dir="./model", output_hidden_states=True)

        self.model.to(self.device)
        self.model.eval()


    def convert_examples_to_features(self, examples, seq_length, tokenizer):
        """Loads a data file into a list of `InputFeature`s."""

        features = []
        for (ex_index, example) in enumerate(examples):
            tokens_a = tokenizer.tokenize(example.text_a)

            tokens_b = None
            if example.text_b:
                tokens_b = tokenizer.tokenize(example.text_b)

            if tokens_b:
                # Modifies `tokens_a` and `tokens_b` in place so that the total
                # length is less than the specified length.
                # Account for [CLS], [SEP], [SEP] with "- 3"
                self._truncate_seq_pair(tokens_a, tokens_b, seq_length - 3)
            else:
                # Account for [CLS] and [SEP] with "- 2"
                if len(tokens_a) > seq_length - 2:
                    tokens_a = tokens_a[0:(seq_length - 2)]

            # The convention in BERT is:
            # (a) For sequence pairs:
            #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
            #  type_ids:   0   0  0    0    0     0      0   0    1  1  1   1  1   1
            # (b) For single sequences:
            #  tokens:   [CLS] the dog is hairy . [SEP]
            #  type_ids:   0   0   0   0  0     0   0
            #
            # Where "type_ids" are used to indicate whether this is the first
            # sequence or the second sequence. The embedding vectors for `type=0` and
            # `type=1` were learned during pre-training and are added to the wordpiece
            # embedding vector (and position vector). This is not *strictly* necessary
            # since the [SEP] token unambigiously separates the sequences, but it makes
            # it easier for the model to learn the concept of sequences.
            #
            # For classification tasks, the first vector (corresponding to [CLS]) is
            # used as as the "sentence vector". Note that this only makes sense because
            # the entire model is fine-tuned.
            tokens = []
            input_type_ids = []
            tokens.append("[CLS]")
            input_type_ids.append(0)
            for token in tokens_a:
                tokens.append(token)
                input_type_ids.append(0)
            tokens.append("[SEP]")
            input_type_ids.append(0)

            if tokens_b:
                for token in tokens_b:
                    tokens.append(token)
                    input_type_ids.append(1)
                tokens.append("[SEP]")
                input_type_ids.append(1)

            input_ids = tokenizer.convert_tokens_to_ids(tokens)

            # The mask has 1 for real tokens and 0 for padding tokens. Only real
            # tokens are attended to.
            input_mask = [1] * len(input_ids)

            # Zero-pad up to the sequence length.
            while len(input_ids) < seq_length:
                input_ids.append(0)
                input_mask.append(0)
                input_type_ids.append(0)

            assert len(input_ids) == seq_length
            assert len(input_mask) == seq_length
            assert len(input_type_ids) == seq_length

            features.append(
                InputFeatures(
                    unique_id=example.unique_id,
                    tokens=tokens,
                    input_ids=input_ids,
                    input_mask=input_mask,
                    input_type_ids=input_type_ids))

        return features


    def _truncate_seq_pair(self, tokens_a, tokens_b, max_length):
        """Truncates a sequence pair in place to the maximum length."""

        # This is a simple heuristic which will always truncate the longer sequence
        # one token at a time. This makes more sense than truncating an equal percent
        # of tokens from each, since if one sequence is very short then each token
        # that's truncated likely contains more information than a longer sequence.
        while True:
            total_length = len(tokens_a) + len(tokens_b)
            if total_length <= max_length:
                break
            if len(tokens_a) > len(tokens_b):
                tokens_a.pop()
            else:
                tokens_b.pop()


    def convert_sequences_to_examples(self, sequences):
        """Converts a list of strings to input examples (accepts ||| separated sequence pairs)."""
        examples = []
        unique_id = 0
        for line in sequences:
            line = line.strip()
            if not line:
                break
            text_a = None
            text_b = None
            m = re.match(r"^(.*) \|\|\| (.*)$", line)
            if m is None:
                text_a = line
            else:
                text_a = m.group(1)
                text_b = m.group(2)
            examples.append(InputExample(unique_id=unique_id, text_a=text_a, text_b=text_b))
            unique_id += 1
        return examples


    def extract_features(self, sequences):
        
        examples = self.convert_sequences_to_examples(sequences)

        features = self.convert_examples_to_features(
            examples=examples, seq_length=self.max_seq_length, tokenizer=self.tokenizer)

        unique_id_to_feature = {}
        for feature in features:
            unique_id_to_feature[feature.unique_id] = feature

        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in features], dtype=torch.long)
        all_example_index = torch.arange(all_input_ids.size(0), dtype=torch.long)

        eval_data = TensorDataset(all_input_ids, all_input_mask, all_example_index)
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=self.batch_size)

        be_result = []

        with torch.no_grad():
            for input_ids, input_mask, example_indices in eval_dataloader:
                input_ids = input_ids.to(self.device)
                input_mask = input_mask.to(self.device)

                model_output = self.model(input_ids, token_type_ids=None, attention_mask=input_mask)
                all_encoder_layers = model_output[2] # layer outputs

                for b, example_index in enumerate(example_indices):
                    feature = features[example_index.item()]
                    unique_id = int(feature.unique_id)

                    # todo:
                    # - pool all tokens instead of CLS
                    # - fine tune on mongodb dataset (NSP + MLM)
                    # - eval on downstream task (CV on OMP categories)
                    CLS_index = 0
                    all_layers = []
                    for (j, layer_index) in enumerate(self.layer_indexes):
                        layer_output = all_encoder_layers[int(layer_index)].detach().cpu().numpy()

                        if(self.use_token):
                            if(self.keep_cls):
                                layer_output = np.mean(layer_output[b, :],axis=0)
                            else:
                                layer_output = np.mean(layer_output[b, CLS_index+1:],axis=0)
                        else:
                            layer_output = layer_output[b,CLS_index]
                        
                        # weighted sum of final j layers
                        all_layers.append(layer_output * self.layer_weights[j])
                    sequence_embedding = np.sum(all_layers, axis=0)

                    be_result.append(sequence_embedding.tolist())

        return be_result

