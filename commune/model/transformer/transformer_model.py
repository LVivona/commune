import os, sys
from pprint import pp

from functools import partial
import asyncio
from copy import deepcopy
from typing import Union, Optional, List
from concurrent import futures
import os, sys
from typing import *
from loguru import logger
import time
from munch import Munch
import argparse
import torch
import json
import random

import streamlit as st


# logger = logger.opt(colors=True)
    
# import torch
import commune
from commune.model import Model
# commune.utils
from torch import nn
# commune.new_event_loop()
from commune.metric import MetricMap

from commune.utils.tokenizer import  decode_topk, get_translation_map, encode_topk, prep_tokenizer

"""
Examples 



"""

shortcuts =  {
    # 0-1B models
    'gpt125m': 'EleutherAI/gpt-neo-125m',

    # 1-3B models
    'gpt2.7b': 'EleutherAI/gpt-neo-2.7B',
    'gpt3b': 'EleutherAI/gpt-neo-2.7B',
    'opt1.3b': 'facebook/opt-1.3b',
    'opt2.7b': 'facebook/opt-2.7b',
    # 'gpt3btuning' : ''

    # 0-7B models
    'gptjt': 'togethercomputer/GPT-JT-6B-v1',
    'gptjt_mod': 'togethercomputer/GPT-JT-Moderation-6B',
    'gptj': 'EleutherAI/gpt-j-6b',
    'gptj.pyg6b': 'PygmalionAI/pygmalion-6b',
    'gpt6b': 'cerebras/Cerebras-GPT-6.7B',
    'gptj.instruct': 'nlpcloud/instruct-gpt-j-fp16',
    'gptj.codegen': 'moyix/codegen-2B-mono-gptj',
    'gptj.hivemind': 'hivemind/gpt-j-6B-8bit',
    'gptj.adventure': 'KoboldAI/GPT-J-6B-Adventure',
    'gptj.pygppo': 'TehVenom/GPT-J-Pyg_PPO-6B', 
    'gptj.alpaca.gpt4': 'vicgalle/gpt-j-6B-alpaca-gpt4',
    'gptj.alpaca': 'bertin-project/bertin-gpt-j-6B-alpaca',
    'oa.galactia.6.7b': 'OpenAssistant/galactica-6.7b-finetuned',
    'opt6.7b': 'facebook/opt-6.7b',
    'llama': 'decapoda-research/llama-7b-hf',
    'vicuna.13b': 'lmsys/vicuna-13b-delta-v0',
    'vicuna.7b': 'lmsys/vicuna-7b-delta-v0',
    'llama-trl': 'trl-lib/llama-7b-se-rl-peft',
    'opt.nerybus': 'KoboldAI/OPT-6.7B-Nerybus-Mix',
    'pygmalion-6b': 'PygmalionAI/pygmalion-6b',
    # # > 7B models
    'oa.pythia.12b': 'OpenAssistant/oasst-sft-1-pythia-12b',
    'gptneox': 'EleutherAI/gpt-neox-20b',
    'gpt20b': 'EleutherAI/gpt-neox-20b',
    'opt13b': 'facebook/opt-13b',
    'gpt13b': 'cerebras/Cerebras-GPT-13B',
    
        }


from torch import nn
class TransformerModel(Model):
    shortcuts = shortcuts
    model_options = list(shortcuts.keys()) + list(shortcuts.values())



    default_tag = 'base'
    
    def __init__(self,
                 config = None,
                 **kwargs
                ):
        
        
        nn.Module.__init__(self) 
        # sets to self.config (with kwargs injected)
        config = self.set_config(config, kwargs=kwargs)
        self.set_stats(config.stats)
        self.set_model(config)
        
    
    def set_tag(self,tag:str):
        if tag is None:
            tag = self.default_tag
        self.tag = self.model_path.replace('/','--')+'--'+tag
    @classmethod
    def calculate_loss( cls, logits: torch.Tensor,
                       input_ids:torch.Tensor,
                       return_value = False,
                       **kwargs) -> torch.Tensor:
        '''
        Calculate the loss for the model.
        '''
        gt = input_ids[:, -(logits.shape[1]-1):].flatten()
        pred = logits[:, :logits.shape[1]-1]
            
        if len(pred.shape) == 3:
            pred = pred.reshape(-1, pred.shape[-1])
        
        assert gt.shape[0] == pred.shape[0], f'gt.shape: {gt.shape} pred.shape: {pred.shape}'

        loss_fn = torch.nn.CrossEntropyLoss()
        loss =  loss_fn(pred, gt.to(pred.device))
        
        # check if loss is nan
        if torch.isnan(loss):
            self.print('Loss is nan, skipping backward pass')
            train = False
            loss = torch.tensor(10)
            raise Exception('Loss is nan, skipping backward pass')
        
        if return_value:
            loss = loss.item()
        
        return loss


    @classmethod
    def generate(cls, text: str = 'hey whadup', max_length: int = 32, **kwargs):
        model = cls.connect('model.gpt125m')
        sample = model.tokenize(text)
        responses = []
        for i in range(max_length):
            output = model.forward(**sample)
            output['logits'] = cls.decode_topk(output['topk'])
            output_ids = torch.argmax(output['logits'][:, -1, :], dim=-1)
            cls.print(output_ids)
            print(output_text)
            responses.append(output_text)
        
        return self.forward(**sample)
    def _forward(self,  
                input_ids: torch.Tensor, 
                attention_mask: torch.Tensor = None,
                topk:int=32,
                output_length:int = None,
                output_hidden_states : bool = True,
                hidden_state_index: int = -1,
                hidden_dim_bounds: List =  [0, -1],
                return_keys:List[str] = ['topk', 'stats'],
                train: bool = False,   
                max_sequence_length : int = None,
                map_tokens: bool = False,
                map_logits: bool = False,  
                tag : str = None,                           
                **kwargs):
        

        # resolve the output length
        output_length = output_length or self.config.output_length or input_ids.shape[1]
        if output_length > input_ids.shape[1]:
            output_length = input_ids.shape[1]
        # resolve the max sequence length (sometimes we want to clip the input to make it faster)
        max_sequence_length = max_sequence_length or self.config.max_sequence_length or input_ids.shape[1]
        attention_mask = attention_mask if isinstance(attention_mask, torch.Tensor) else torch.ones_like(input_ids)


        sample = {
        'input_ids': input_ids[:, -max_sequence_length:],
        'attention_mask': attention_mask,
        }
        
        if map_tokens:
            offset_mapping, offset_mapping_std, original_input_ids = None, None, None
            original_input_ids = self.copy(sample['input_ids'])
            tokens = self.token_translator.translate_tokens(input_ids=sample['input_ids'], return_offsets_mapping=True)
            offset_mapping = tokens.offset_mapping
            offset_mapping_std = tokens.offset_mapping_std
            sample['input_ids'] = tokens.input_ids
            sample['attention_mask'] = tokens.attention_mask
        
        for k,v in sample.items():
            if isinstance(v, torch.Tensor):
                sample[k] = sample[k].to(self.device)
        
        
        # clip the input ids to the vocab size
        sample['input_ids'] = torch.clip(sample['input_ids'], 0, self.tokenizer.vocab_size-1)
        if train:
            self.optimizer.zero_grad()
            
        device = self.get_model_device(self.model)
        
        stats = self.copy(self.stats)
        stats['time'] =  self.time()
        sample['input_ids'] = sample['input_ids'].to(device)
        
        good_logits = False
        model_output = self.model(input_ids=sample['input_ids'].to(device),
                                output_hidden_states=output_hidden_states)
        
        # output_dict = self.process_output(model_output)
        # check if there are any nans in the logits
        logits_has_nans =  torch.isnan(model_output.logits).any()
        if logits_has_nans:
            raise Exception('logits has nans with sample input_ids: ', sample['input_ids'])
                
        # sometime we dont care about the begginning of the sequence
        output_length = output_length if output_length else model_output.logits.size(1)
        
        output_dict = {}
        output_dict['logits']= model_output.logits[:,-output_length:,:]
        
        if map_logits:
            output_dict['logits'] = self.token_translator.translate_logits(logits = output_dict['logits'],
                                                                           offset_mapping=offset_mapping_std,
                                                                           offset_mapping_std=offset_mapping_std,
                                                                           tokens=sample['input_ids'],
                                                                           tokens_std=original_input_ids)
            
        output_dict['topk']=self.encode_topk(output_dict['logits'], topk=topk)
        
        if isinstance(hidden_state_index, int):
            hidden_state_index = [hidden_state_index]
        output_dict['hidden_states'] = [model_output.hidden_states[h_idx] for h_idx in hidden_state_index]
        
        output_dict['input_ids'] = sample['input_ids']
        output_dict['loss'] = self.calculate_loss(**output_dict)
        loss = output_dict['loss']
        
        # check if loss is nan
        if torch.isnan(loss):
            self.print('Loss is nan, skipping backward pass')
            train = False
            loss = torch.tensor(10)
            raise Exception('Loss is nan, skipping backward pass')
        
        input_tokens = input_ids.shape[0]*input_ids.shape[1]
        input_samples = input_ids.shape[0]
        
    
        
        if train:
            loss.backward()
            self.optimizer.step()
            loss = loss.item()
            stats['train_samples'] = stats.get('train_samples', 0) + input_samples
            stats['train_tokens'] = stats.get('train_tokens',0) + input_tokens
            stats['train_steps'] = stats.get('train_steps', 0) + 1
            stats['epoch_length'] = self.config.epoch_length
            stats['batch_count'] = stats['train_steps'] % stats['epoch_length']
            stats['lr'] = self.config['optimizer']['lr']
            
            # calculalte the epoch loss
            stats['epoch_loss'] = (stats.get('epoch_loss', 0)*(stats['train_steps']-1) + loss)/stats['train_steps']
        else:
            loss = loss.item()
        
        stats['latency'] = self.round(self.time() - stats['time'], sig=2)
        stats['inference_steps'] = stats.get('inference_steps', 0) + 1
        stats['inference_samples'] = stats.get('inference_samples', 0) + input_samples
        stats['inference_tokens'] = stats.get('inference_tokens',0) + input_tokens
        stats['inference_steps'] = stats.get('inference_steps', 0) + 1
        
        past_loss = stats.get('loss', loss)
        alpha = 1 / self.config.evaluation_steps
        stats['loss'] = (past_loss*(1-alpha) + alpha*loss)

        stats['sample_loss'] = loss
        stats['input_shape'] = list(input_ids.shape)
        stats['train'] = train
        stats = self.register_stats(stats)
        
        output_dict['stats'] = self.munch2dict(stats)
        output_dict['stats'].pop('epoch_loss_history', None)
        
        return {key:output_dict[key] for key in return_keys}
        
    def register_stats(self, stats):
        stats['epoch'] = stats.get('epoch', 0)
        stats['saved_step'] = stats.get('saved_step', 0)
        stats['steps_since_best'] = stats.get('steps_since_best', 10e10)
        stats['best_loss'] = stats.get('best_loss', self.config.default_metric)
        stats['history'] = stats.get('history', [])

        if stats['train'] and stats['batch_count'] == 0:
            timestamp = self.time()
            prev_epoch_loss_history = stats.get('epoch_loss_history', [{'loss': self.config.default_metric, 'time': timestamp}])
            stats['epoch_loss_history'] =stats.get('epoch_loss_history',[]) + [{'loss': stats['epoch_loss'], 'time': timestamp}]
            stats['epoch'] = stats['epoch'] + 1

            # check if the loss is better than the best loss
            is_better = self.is_better(stats)

            stats['steps_since_save'] = stats['train_steps'] - stats['saved_step']
            if is_better:
                if stats['steps_since_save'] >= self.config.epoch_length:
                    self.save()
                    stats['saved_step'] = stats['train_steps']
                    
                stats['steps_since_best'] = 0
                stats['best_loss'] = stats['loss']
            else:
                stats['steps_since_best'] = stats['steps_since_best'] + 1

                
            if stats['steps_since_best'] >= self.config.reload_patience:
                stats['steps_since_best'] = 0
                self.load(keys=['model', 'optimizer'])
            
        
        
        stats['history'] = self.stats.get('history', []) + [stats]
        stats['history'][-1].pop('history', None)
        self.set_stats(stats)
        

            
        return stats
    
    def is_better(self, stats) -> bool:
        return stats['loss'] <= stats['best_loss']

    def set_model(self, config) -> None:
        if config == None:
            config = self.config
        
        from transformers import  AutoModelForCausalLM, AutoModel, AutoConfig
        from accelerate import init_empty_weights

        self.model_path = config['model_path'] = self.shortcuts.get(config['model'], config['model'])

        model = self.get_empty_model(self.model_path)
        config.model_size = self.get_model_size(model)
        config.excpeted_model_size = config.model_size*self.config.model_inflation_ratio
      
        free_gpu_memory = self.free_gpu_memory()

              
        if config.max_memory == None:
            config.max_memory = self.max_gpu_memory(memory=config.excpeted_model_size,
                                                max_gpu_ratio=config.max_gpu_ratio,
                                                reserve=config.reserve_gpus)
            
        config.max_memory = {k:free_gpu_memory[k] for k,v in config.max_memory.items()}

        if config.device_map == None:
            config.device_map= self.infer_device_map(model, max_memory=config.max_memory)
        
        verbose = config.verbose
        

        if isinstance(config.device_map, dict):
            config.device_map = {k:v for k,v in config.device_map.items() }

        model_kwargs=dict(
            max_memory=config.max_memory,
            device_map= config.device_map,
        )
        
        if verbose:
            self.print(f'model_kwargs: {model_kwargs}')
       
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path, **model_kwargs) 
        
        config.devices = list(set(list(self.model.hf_device_map.values())))
        config.device = config.devices[0]

        self.device_map = config.device_map 
        self.devices = config.devices
        self.device = config.device
        
        if config.reserve_gpus:
            self.unreserve_gpus(config.max_memory)
        
        self.set_tokenizer(config.tokenizer)
        self.set_optimizer(config.optimizer)
        self.set_finetune(config.finetune) 
          
        self.set_tag(config.tag)
        self.set_stats(config.stats)    
        self.set_epoch_length(config.epoch_length)      
          
        if config.load:
            self.load() 
            
        self.config = config


    def set_epoch_length(self, epoch_length:int) -> int:
        assert isinstance(epoch_length, int)
        self.epoch_length = self.epoch_size = self.config['epoch_length']=  epoch_length
        return self.epoch_length
    set_epoch_size = set_epoch_length

    def set_tokenizer(self, tokenizer):
        from transformers import AutoTokenizer, AutoModel
        from commune.utils.tokenizer import prep_tokenizer

        if tokenizer is None:
            tokenizer = self.model_path
            
        assert isinstance(tokenizer, str)
        self.print(f'setting {tokenizer} tokenizer...')
        assert isinstance(tokenizer, str, )
        tokenizer = self.shortcuts.get(tokenizer, tokenizer)
        self.config['tokenizer'] = tokenizer
        
        try:
            # HACK TO INCLUDE LLAMA TOKENIZER
            tokenizer = AutoTokenizer.from_pretrained(tokenizer, use_fast= True)
        except ValueError:
            
            print('resorting ot use_fast = False')
            tokenizer = AutoTokenizer.from_pretrained(tokenizer, use_fast=False)


        self.tokenizer = tokenizer
        
    
        self.std_tokenizer = AutoTokenizer.from_pretrained('gpt2', use_fast= True)
        self.tokenizer = prep_tokenizer(self.std_tokenizer)
        self.tokenizer = prep_tokenizer(self.tokenizer, self.std_tokenizer)
        self.token_translator = self.get_module('model.token_translator')(tokenizer=tokenizer, std_tokenizer=self.std_tokenizer)

        return self.tokenizer

    
    
    @staticmethod
    def encode_topk( forward_response_tensor: torch.Tensor , topk:int=4096) -> torch.Tensor:
        """ Returns topk tokens/probabilities given unnormalized logits as input. """

        #import ipdb; ipdb.set_trace()

        logits = forward_response_tensor  # unnormalized logit scores: [batch_size, sequence_len, vocab_size]
        probs = torch.softmax(logits, dim=-1).to(torch.float32)  # normalized probabilities: [batch_size, sequence_len, vocab_size]

        topk_indices = torch.argsort(probs, dim=-1, descending=True)[...,:topk]
        # topk_values, topk_indices = torch.topk(probs, topk) # topk probs and indices: [batch_size, sequence_len, topk]

        topk_values = probs.gather( index=topk_indices, dim=-1)
        encoded_probs = torch.cat([topk_values, topk_indices], dim=-1)  # [batch_size, sequence_len, topk + topk]
        return encoded_probs  # [batch_size, sequence_len, topk + topk]


    @staticmethod
    def decode_topk(  forward_response_tensor: torch.Tensor, topk:int=4096, vocab_size:int=50257) -> torch.Tensor:
        """ Returns full logits by decoding topk-encoding input. """
        batch_size, sequence_len, _ = forward_response_tensor.shape
        encoded_probs = forward_response_tensor  # encoded probabilities: [batch_size, sequence_len, topk + topk]
        topk_values = encoded_probs[..., :topk]  # topk probs: [batch_size, sequence_len, topk]
        topk_indices = encoded_probs[..., topk:].long()  # topk probs indices: [batch_size, sequence_len, topk]

        topk_pmass = topk_values.sum(dim=-1)  # topk probability mass: [batch_size, sequence_len]
        remainder_pmass = torch.clamp(1 - topk_pmass, 1e-40, 1)  # remainder probability mass: [batch_size, sequence_len]
        remainder_floor = remainder_pmass / (vocab_size - topk)  # divide remainder: [batch_size, sequence_len]

        logits = torch.ones((batch_size, sequence_len, vocab_size), dtype=topk_values.dtype).to(topk_values.device)
        logits *= torch.log(remainder_floor)[:, :, None]  # set probability floor: [batch_size, sequence_len, vocab_size]

        logits.scatter_(-1, topk_indices, torch.log(topk_values + 1e-40))  # insert topk probs: [batch_size, sequence_len, vocab_size]

        return logits  # [batch_size, sequence_len, vocab_size]


    def tokenizer_name(self):
        return self.config['tokenizer']

    def tokenize(self, text: str = 'Whadup',
                 padding=True, 
                 truncation=True, 
                 max_length=64,
                 return_tensors='pt',
                 add_special_tokens=False,
                 device:str = None, 
                 **kwargs) -> torch.Tensor:
        """ Returns tokenized text as torch tensor. """
        
        sample = self.tokenizer(text, 
                                             padding=padding, 
                                             truncation=truncation, 
                                             max_length=max_length, 
                                             return_tensors=return_tensors,
                                             add_special_tokens=add_special_tokens, 
                                             **kwargs)  # assume tokenizer.padding_side = 'left'

        device = device if device != None else self.device
        
        sample = dict(
            input_ids= sample['input_ids'].to(device),
            attention_mask= sample['attention_mask'].to(device)
        )
        
        return sample



    def detokenize(self, input_ids: torch.Tensor, **kwargs) -> torch.Tensor:
        """ Returns tokenized text as torch tensor. """
        
        text = self.tokenizer.batch_decode(input_ids,**kwargs)  # assume tokenizer.padding_side = 'left'

        return text
    


    @classmethod
    def train(cls, model = 'gpt125m', 
             topk:int=256 ,
             dataset:str = 'dataset.bittensor',
             num_batches = 1000,
             sequence_length : int = 256,
             batch_size: int = 32,
             autocast : bool = True,
             train: bool= True,
             map_logits : bool = False,
             map_tokens : bool = False,
             timeout : int= 60,
             remote:bool = False,
             **kwargs
             ):
        
        if remote:
            kwargs = cls.get_params(locals())
            kwargs['remote'] = False
            return cls.remote_fn(fn='train',kwargs=kwargs, name=f"train::{model}")
        
        
        if isinstance(model, str):
            if model in cls.model_options:
                model = cls(model=model)
            else:
                model  = cls.connect(model)  
        
        
        
        def sample_check(sample):
            return bool(isinstance(sample, dict) and 'input_ids' in sample)
        

        if isinstance(dataset, str):
            dataset = commune.connect(dataset)
        for i in range(num_batches):
            try:

                sample = dataset.sample(batch_size=batch_size,
                                        sequence_length=sequence_length)
            except Exception as e:
                cls.print(f'Skipping batch for this reason fam ({e})')
                continue

            if not sample_check(sample):
                cls.print('Sample check failed, skipping batch')
                continue
        
            sample.update(
                topk=topk,
                map_tokens=map_tokens,
                map_logits=map_logits,
                train=train,
                autocast=autocast,
                timeout=timeout,
                return_keys=[ 'topk', 'stats']
            )
            try:
                output = model.forward(**sample)
                cls.print('STATS: ' ,output.get('stats', 'Not Stats'))
            except Exception as e:
                raise e
          
          

    @classmethod
    def train_fleet(cls, model = 'model', num_batches=2, dataset='dataset.bittensor',  **kwargs):
        model_pool = commune.connect_pool(model)
        models = list(model_pool.values())
        model_names = list(model_pool.keys())
        for model, model_name in zip(models, model_names):
            cls.print(f"Training {model_name} on {dataset} for {num_batches} batches")
            cls.train(model=cls.choice(models), dataset=dataset, num_batches=num_batches,**kwargs)

    test = train 



    @classmethod
    def models(cls):
        return list(cls.shortcuts.keys())
    
    
    
    @classmethod
    def default_models(cls):
        return list(cls.shortcuts.keys())
          
          
    fleet_group = {
        
        '0': [ 'gpt125m', 'gpt2.7b', 'opt2.7b','gptj'],
        '1': [ 'gptj.alpaca', 'gptj.pygppo', 'opt6.7b', 'oa.galactia.6.7b', 'vicuna.7b', 'gptj'],
        '2': [ 'gptj.instruct', 'gpt6b', 'opt6.7b', 'oa.galactia.6.7b', 'vicuna.7b', 'gptj'],


        # '0': ['vicuna.7b', 'opt6.7b', 'oa.galactia.6.7b'],

        'all': default_models,
        'default': default_models,
    }
    @classmethod
    def deploy_fleet(cls, 
                     model = 'gptj',
                     tags= ['alice', 'bob', 'chris', 'dan', 'elon', 'frank', 'greg', 'huck' ], 
                     **kwargs
                     ) -> List[str]:
        tag_seperator = kwargs.get('tag_seperator', '::')
        free_gpu_memory = cls.free_gpu_memory()
        deployed_models = []
        models = [ model+tag_seperator+t for t in tags]
        cls.deploy(*models, **kwargs)
        return models
        
    @classmethod
    def undeployed_models(cls, models: List[str] = 'all'):
        models = cls.fleet_group.get(models, models)
        undeployed_models = []
        for model in models:
            if cls.module_exists(f'model.{model}') == False:
                undeployed_models.append(model)
        return undeployed_models
       
    
    @classmethod   
    def infer_device_map(cls, model, 
                         max_memory: dict = None,
                         **kwargs,
                         ):
        if max_memory == None:
            max_memory = cls.max_gpu_memory()    
            
        from accelerate import infer_auto_device_map
        if isinstance(model, str):
            model = cls.get_empty_model(model)
        device_map = infer_auto_device_map(model, max_memory=max_memory, **kwargs) 
        return device_map
    
    
    @classmethod
    def get_empty_model(cls, model):
        from transformers import  AutoModelForCausalLM, AutoModel, AutoConfig
        from accelerate import init_empty_weights
        
        model = cls.shortcuts.get(model, model)

        if isinstance(model, str):
            print(f'loading config model from {model}...')

            model_config = AutoConfig.from_pretrained(model)
            model_config_dict = model_config.to_dict()
            with init_empty_weights():
                model = AutoModelForCausalLM.from_config(model_config)
                
        return model
    
    
        
      
    @classmethod
    def deploy(cls,
               *models: str,
               name: str =None, 
               wait_for_server: bool = False, 
               device = None, 
               replace:bool = True,
               mode:str = 'pm2',
               tag_seperator:str = '::',               
               
               **kwargs):


        tag = kwargs.get('tag', None)
        assert len(models) > 0
        model_names = []
        
        free_gpu_memory = cls.free_gpu_memory()
        
        config = cls.get_config(kwargs=kwargs)
        for model in models:
            if tag_seperator in model:
                model, tag = model.split(tag_seperator)
            name = f'model.{model}'
            if tag == None:
                tag =  'base'
            if tag:
                name = name+tag_seperator+str(tag)
    
            model_size_bytes = cls.get_model_size(model)*config.model_inflation_ratio
            max_gpu_memory = cls.max_gpu_memory(model_size_bytes,
                                                max_gpu_ratio=config.max_gpu_ratio ,
                                                free_gpu_memory=free_gpu_memory)
            
            for k,v in max_gpu_memory.items():
                free_gpu_memory[k]-= v
                free_gpu_memory[k] = max(0, free_gpu_memory[k])
            devices = list(max_gpu_memory.keys())
            cls.print(devices)
            # cls.print(commune.reserved_gpus(), 'fam') 
            config.model = model
            config.tag = tag
            kwargs = {'config': config, 'tag': tag}
            
            cls.launch(name=name,
                       kwargs=kwargs,
                       mode=mode, 
                       refresh=True,
                       device=device, 
                       wait_for_server=wait_for_server,
                       verbose=False)
            
            
            
            model_names.append(name) 
            
        return model_names
            
    @classmethod
    def sandbox(cls):
        self = cls(model='opt2.7b')
        

        
if __name__ == "__main__":
    
    TransformerModel.run()


