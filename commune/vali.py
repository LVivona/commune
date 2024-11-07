
import commune as c
import os
import pandas as pd
from typing import *

class Vali(c.Module):
    endpoints = ['eval_module', 'score', 'eval', 'leaderboard']
    voting_networks = ['bittensor', 'commune', 'subspace']
    networks = ['local'] + voting_networks
    subnet_splitters = ['.', '/', ':']

    def __init__(self,
                    network= 'local', # for local subspace:test or test # for testnet subspace:main or main # for mainnet
                    subnet = None,
                    search=  None, # (OPTIONAL) the search string for the network 
                    verbose=  True, # the verbose mode for the worker # EPOCH
                    batch_size= 16,
                    max_workers=  None ,
                    score = None, # score function
                    path= None, # the storage path for the module eval, if not null then the module eval is stored in this directory
                    alpha= 1.0, # alpha for score
                    min_score=  0, # the minimum weight of the leaderboard
                    run_loop= True, # This is the key that we need to change to false
                    test= False, # the test mode for the validator
                    module = None,
                    info_fn = 'info', 
                    max_age= 120, # the maximum age of the network
                    timeout= 2, # timeout per evaluation of the module
                    update=False,
                    key = None,
                 **kwargs):
        config = self.set_config(locals())
        config = c.dict2munch({**Vali.config(), **config})
        self.config = config
        self.epochs = 0
        self.epoch_start_time = 0
        self.set_key(key)
        self.set_score(score)
        self.set_network(update=update)
        if config.run_loop:
            c.thread(self.run_loop)

    init_vali = __init__
    def score(self, module):
        return 'name' in module.info()

    def set_score(self, score: Union[Callable, str] ):
        score = score or  self.score
        if isinstance(score, str):
            if hasattr(self, score):
                score = getattr(self, score)
            else:
                score = c.obj(score)
        assert callable(score), f'{score} is not callable'
        setattr(self, 'score', score )
        return {'success': True, 'msg': 'Set score function', 'score': self.score.__name__}
    
    @property
    def is_voting_network(self):
        return any([v in self.config.network for v in self.voting_networks])
    
    def run_loop(self):
        while True:
            from tqdm import tqdm
            time_to_wait = int(max(0,self.epoch_start_time - c.time() + self.config.tempo))
            desc = f'Waiting Next Epoch ({self.epochs}) with Tempo {self.config.tempo}'
            print(f'Time Until Next Epoch --> {time_to_wait}')
            [ c.sleep(1) for _ in tqdm(range(time_to_wait), desc=desc)]
            try:
                self.epoch()
                c.print(self.vote())
                c.print(self.leaderboard())
            except Exception as e:
                c.print('ERROR IN THE self.epoch',c.detailed_error(e))

    def get_next_result(self, futures):
        try:
            for future in c.as_completed(futures, timeout=self.config.timeout):
                futures.remove(future) 
                result = future.result()
                result['score'] = result.get('score', 0)
                did_score_bool = bool(result['score'] > 0)
                emoji =  '🟢' if did_score_bool  else '🔴'
                if did_score_bool:
                    keys = ['score', 'name', 'address', 'latency', 'key', 'crypto_type']
                else:
                    keys = list(result.keys())
                result = {k: result.get(k, None) for k in keys if k in result}
                msg = ' '.join([f'{k}={result[k]}' for k in result])
                break
        except Exception as e:
            emoji = '🔴'
            result = c.detailed_error(e)
            msg = f'ERROR IN BATCH({result})'
        c.print(f'{emoji}RESULT({msg}){emoji}', color='cyan', verbose=self.config.verbose)

            
        return result

    epoch2results = {}

    def epoch(self, network=None,  df=True, **kwargs):
        futures = []
        self.epoch_start_time = c.time()
        self.set_network(network=network, **kwargs)
        self.executor = c.module('executor')(max_workers=self.config.max_workers, maxsize=self.config.batch_size)
        c.print(f'Epoch {self.epochs} with {self.n} modules', color='yellow')
        results = []
        progress = c.tqdm(total=self.n, desc='Evaluating Modules')
        for module_address in c.shuffle(list(self.namespace.values())):
            c.print(f'EVALUATING({module_address})🟡', color='cyan', verbose=self.config.verbose)
            if self.executor.is_full:
                results.append(self.get_next_result(futures))
            else:
                futures.append(self.executor.submit(self.eval_module, [module_address], timeout=self.config.timeout))
            progress.update(1)
        while len(futures) > 0:
            results.append(self.get_next_result(futures))
        results = [r for r in results if r.get('score', 0) > 0]
        if df:
            if len(results) > 0 and 'score' in results[0]:
                results = c.df(results).sort_values(by='score', ascending=False)
        self.epochs += 1
        return results

    @property
    def network_staleness(self) -> int:
        """
        The staleness of the network
        """
        return c.time() - self.network_time
    

    def filter_module(self, module:str):
        search = self.config.search
        if ',' in str(search):
            search_list = search.split(',')
        else:
            search_list = [search]
        return all([s == None or s in module  for s in search_list ])

    def set_network(self, network:str=None, update = False,tempo=None):
        config = self.config
        network = network or config.network
        for subnet_splitter in self.subnet_splitters:
            if subnet_splitter in network:
                network, subnet = network.split(subnet_splitter)
                break
        subnet = config.subnet
        path = self.config.path
        if path == None:
            path = network if subnet == None else f'{network}/{subnet}' 
        path = self.resolve_path(path)
        network_path = path + '/network_state'
        max_age = config.max_age
        network_state = c.get(network_path, max_age=max_age, update=update)
        self.path = path

        # RESOLVE THE VOTING NETWORKS
        has_network_module = bool(hasattr(self, 'network_module') and network == self.config.network)
        network_module = c.module(network)() if not has_network_module else self.network_module
        if 'local' in network:
            # local network does not need to be updated as it is atomically updated
            namespace = network_module.namespace(max_age=max_age)
            params = network_module.params()
        elif 'subspace' in network:
            # the network is a voting network
            subnet2netuid = network_module.subnet2netuid()
            namespace = network_module.namespace(subnet=subnet, max_age=max_age)
            params = network_module.subnet_params(subnet=subnet, max_age=max_age)
            config.netuid = subnet2netuid.get(subnet, None)
            config.subnet = subnet
            config.tempo = params.get('tempo', self.config.tempo)
        else:
            raise ValueError(f'Network {network} is not a valid network')
        n = len(namespace)
        network_state = {
            'network': network,
            'subnet': subnet,
            'n': n,
            'time': c.time(),
            'params': params,
            'namespace': namespace,
        }

        self.network_module = network_module
        self.n  = len(namespace)  
        self.namespace = {k: v for k, v in namespace.items() if self.filter_module(k)}
        self.network = config.network = network
        self.config = config

        c.put(network_path, network_state)
        c.print(f'Network(network={config.network}, subnet={config.subnet} n={self.n})')

        return network_state

    module2last_update = {}

    def check_info(self, info:dict) -> bool:
        return bool(isinstance(info, dict) and all([k in info for k in  ['score', 'address', 'name', 'key']]))

    def eval_module(self,  module:str, **kwargs):
        address = self.namespace.get(module, module)
        path = self.path +'/'+ address
        module_client = c.connect(address, key=self.key)
        info = self.get_json(path, {})
        if not self.check_info(info):
            info =  getattr(module_client, self.config.info_fn)()
        info['timestamp'] = c.time() # the timestamp
        last_score = info.get('score', 0)
        response = self.score(module_client, **kwargs)
        response = {'score': float(response)} if type(response) in [int, float, bool] else response
        info['latency'] = c.round(c.time() - info['timestamp'], 3)
        info.update(response)
        info['score'] = info['score']  * self.config.alpha + last_score * (1 - self.config.alpha)
        if response['score'] > self.config.min_score:
            self.put_json(path, info)
        return info
    
    eval = eval_module

    def votes(self, **kwargs):
        votes = {'modules': [], 'weights': []}
        for module in self.leaderboard().to_records():
            if module['score'] > 0:
                votes['modules'] += [module['key']]
                votes['weights'] += [module['score'].item()]
        return votes
    
    @property
    def votes_path(self):
        return self.path + f'/votes'

    def vote(self, update=False, **kwargs):
        if not self.is_voting_network :
            return {'success': False, 'msg': f'{self.network} is not a voting network ({self.voting_networks})'}
            
        if not hasattr(self, 'vote_time'):
            self.vote_time = 0
        vote_staleness = c.time() - self.vote_time
        if not update:
            if vote_staleness < self.config.tempo:
                return {'success': False, 'msg': f'Vote is too soon {vote_staleness}'}
        votes =self.votes() 
        return self.network_module.vote(modules=votes['modules'], # passing names as uids, to avoid slot conflicts
                            weights=votes['weights'], 
                            key=self.key, 
                            subnet=self.config.subnet,
                            )
    
    set_weights = vote 

    def module_info(self, **kwargs):
        if hasattr(self, 'network_module'):
            return self.network_module.module_info(self.key.ss58_address, netuid=self.config.netuid, **kwargs)
        else:
            return {}
    
    def leaderboard(self,
                    keys = ['name', 'score', 'latency',  'address', 'key'],
                    ascending = True,
                    by = 'score',
                    to_dict = False,
                    n = None,
                    page = None,
                    **kwargs
                    ):
        max_age = self.config.tempo
        paths = self.paths()
        df = []
        # chunk the jobs into batches
        for path in paths:
            r = self.get(path, {},  max_age=max_age)
            if isinstance(r, dict) and 'key' and  r.get('score', 0) > self.config.min_score  :
                df += [{k: r.get(k, None) for k in keys}]
            else :
                # removing the path as it is not a valid module and is too old
                self.rm(path)

        df = c.df(df) 
        if len(df) > 0:
            if isinstance(by, str):
                by = [by]
            df = df.sort_values(by=by, ascending=ascending)
            if n != None:
                if page != None:
                    df = df[page*n:(page+1)*n]
                else:
                    df = df[:n]
        # if to_dict is true, we return the dataframe as a list of dictionaries
        if to_dict:
            return df.to_dict(orient='records')

        return df

    def paths(self):
        paths = self.ls(self.path)
        return paths
    
    def refresh_leaderboard(self):
        path = self.path
        c.rm(path)
        df = self.leaderboard()
        assert len(df) == 0, f'Leaderboard not removed {df}'
        return {'success': True, 'msg': 'Leaderboard removed', 'path': path}
    
    refresh = refresh_leaderboard

    @staticmethod
    def test(  n=2, tag = 'vali_test_net',  miner='module', vali='vali',  path = '/tmp/commune/vali_test',network='local'):
        
        test_miners = [f'{miner}::{tag}_{i}' for i in range(n)]
        modules = test_miners
        search = tag
        for m in modules:
            c.kill(m) 
        for m in modules:
            c.print(c.serve(m))
        namespace = c.namespace(search=search)
        while len(namespace) < n:
            namespace = c.namespace(search=search)
        leaderboard = Vali.run_epoch(network=network, search=search, path=path)
        assert len(leaderboard) == n, f'Leaderboard not updated {leaderboard}'
        for miner in modules:
            c.print(c.kill(miner))
        return {'success': True, 'msg': 'subnet test passed'}
    
    def __del__(self):
        c.print('Cancelling futures')
        return {'success': True, 'msg': 'Cancelling futures'}

    @classmethod
    def run_epoch(cls, run_loop=False, **kwargs):
        return  cls( run_loop=run_loop, **kwargs).epoch(df=1)
