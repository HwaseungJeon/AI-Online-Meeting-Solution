# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_data-core.ipynb (unless otherwise specified).

__all__ = ['HF_BaseInput', 'HF_BeforeBatchTransform', 'HF_AfterBatchTransform', 'HF_TextBlock', 'get_blurr_tfm']

# Cell
from functools import reduce

import torch,pdb
from transformers import *
from fastai.text.all import *

from ..utils import *

logging.set_verbosity_error()

# Cell
class HF_BaseInput(TensorBase):

    def show(self, hf_tokenizer, ctx=None, trunc_at=None, **kwargs):
        input_ids = self.cpu().numpy()
        decoded_input = str(hf_tokenizer.decode(input_ids, skip_special_tokens=True))[:trunc_at]

        return show_title(decoded_input, ctx=ctx, label='text')

# Cell
class HF_BeforeBatchTransform(Transform):
    """Handles everything you need to assemble a mini-batch of inputs and targets, as well as
    decode the dictionary produced as a byproduct of the tokenization process in the `encodes` method.
    """
    def __init__(self, hf_arch, hf_config, hf_tokenizer, hf_model,
                 max_length=None, padding=True, truncation=True, is_split_into_words=False,
                 tok_kwargs={}, **kwargs):

        store_attr(self=self, names='hf_arch, hf_config, hf_tokenizer, hf_model')
        store_attr(self=self, names='max_length, padding, truncation, is_split_into_words, tok_kwargs')
        store_attr(self=self, names='kwargs')

    def encodes(self, samples):
        samples = L(samples)

        # grab inputs
        if (is_listy(samples[0][0]) and not self.is_split_into_words):
            inps = list(zip(samples.itemgot(0, 0), samples.itemgot(0, 1)))
        else:
            inps = samples.itemgot(0).items

        # tokenize
        tok_d = self.hf_tokenizer(inps,
                                  max_length=self.max_length,
                                  padding=self.padding,
                                  truncation=self.truncation,
                                  is_split_into_words=self.is_split_into_words,
                                  return_tensors='pt',
                                  **self.tok_kwargs)

        # update samples with tokenized inputs (e.g. input_ids, attention_mask, etc...)
        d_keys = tok_d.keys()
        updated_samples= [ (*[{k: tok_d[k][idx] for k in d_keys}], *sample[1:])
                          for idx, sample in enumerate(samples) ]

        return updated_samples

# Cell
class HF_AfterBatchTransform(Transform):

    def __init__(self, hf_tokenizer, input_return_type=HF_BaseInput):
        store_attr(self=self, names='hf_tokenizer, input_return_type')

    def decodes(self, encoded_samples):
        if (isinstance(encoded_samples, dict)):
            return self.input_return_type(encoded_samples['input_ids'], hf_tokenizer=self.hf_tokenizer)
        return encoded_samples

# Cell
class HF_TextBlock(TransformBlock):

    def __init__(self, hf_arch=None, hf_config=None, hf_tokenizer=None, hf_model=None,
                 before_batch_tfm=None, after_batch_tfm=None,
                 max_length=None, padding=True, truncation=True, is_split_into_words=False,
                 input_return_type=HF_BaseInput, dl_type=SortedDL,
                 before_batch_kwargs={}, after_batch_kwargs={}, tok_kwargs={}, **kwargs):

        if((not all([hf_arch, hf_config, hf_tokenizer, hf_model])) and before_batch_tfm is None):
            raise ValueError("""You must supply the huggingfrace architecture, config, tokenizer, and model
                                - or - an instances of HF_BeforeBatchTransform""")

        if (before_batch_tfm is None):
            before_batch_tfm = HF_BeforeBatchTransform(hf_arch, hf_config, hf_tokenizer, hf_model,
                                                       max_length=max_length,
                                                       padding=padding,
                                                       truncation=truncation,
                                                       is_split_into_words=is_split_into_words,
                                                       tok_kwargs=tok_kwargs.copy(),
                                                       **before_batch_kwargs.copy())

        # as we'll have our HF_BeforeBatchTransforme by now, we'll use it to set the TransformBlock's
        # huggingface face objects
        self.hf_arch = before_batch_tfm.hf_arch
        self.hf_config = before_batch_tfm.hf_config
        self.hf_tokenizer = before_batch_tfm.hf_tokenizer
        self.hf_model = before_batch_tfm.hf_model

        if (after_batch_tfm is None):
            after_batch_tfm = HF_AfterBatchTransform(self.hf_tokenizer, input_return_type,
                                                     **after_batch_kwargs.copy())

        return super().__init__(dl_type=dl_type,
                                dls_kwargs={ 'before_batch': before_batch_tfm },
                                batch_tfms=after_batch_tfm)

# Cell
def get_blurr_tfm(tfms_list, tfm_class=HF_BeforeBatchTransform):
    return next(filter(lambda el: issubclass(type(el), tfm_class), tfms_list), None)

# Cell
@typedispatch
def show_batch(x:HF_BaseInput, y, samples, dataloaders, ctxs=None, max_n=6, trunc_at=None, **kwargs):
    # grab our tokenizer and pass it and "trunc_at" to HF_BaseInput.show via kwargs
    hf_before_batch_tfm = get_blurr_tfm(dataloaders.before_batch)
    kwargs['hf_tokenizer'] = hf_before_batch_tfm.hf_tokenizer
    kwargs['trunc_at'] = trunc_at

    if ctxs is None: ctxs = get_empty_df(min(len(samples), max_n))
    ctxs = show_batch[object](x, y, samples, max_n=max_n, ctxs=ctxs, **kwargs)

    display_df(pd.DataFrame(ctxs))
    return ctxs