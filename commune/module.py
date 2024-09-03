import os
import inspect
import json
import shutil
import time
import gc
import threading
import subprocess
import shlex
import sys
import argparse
import asyncio
import nest_asyncio
import urllib
import requests
import netaddr
import yaml
from functools import partial
import random
import os
from copy import deepcopy
import concurrent
from typing import *


import socket

nest_asyncio.apply()

class c:

    whitelist = []
    _schema = None
    core_modules = ['module', 'key', 'subspace', 'web3', 'serializer', 'pm2',  
                    'executor', 'client', 'server', 
                    'namespace' ]
    libname = lib_name = lib = 'commune' # the name of the library
    cost = 1
    description = """This is a module"""
    base_module = 'module' # the base module
    giturl = 'https://github.com/commune-ai/commune.git' # tge gutg
    root_module_class = 'c' # WE REPLACE THIS THIS Module at the end, kindof odd, i know, ill fix it fam, chill out dawg, i didnt sleep with your girl
    default_port_range = [50050, 50150] # the port range between 50050 and 50150
    default_ip = local_ip = loopback = '0.0.0.0'
    address = '0.0.0.0:8888' # the address of the server (default)
    rootpath = root_path  = root  = '/'.join(__file__.split('/')[:-2])  # the path to the root of the library
    homepath = home_path = os.path.expanduser('~') # the home path
    libpath = lib_path = os.path.dirname(root_path) # the path to the library
    repopath = repo_path  = os.path.dirname(root_path) # the path to the repo
    cache = {} # cache for module objects
    home = os.path.expanduser('~') # the home directory
    __ss58_format__ = 42 # the ss58 format for the substrate address
    cache_path = os.path.expanduser(f'~/.{libname}')
    default_tag = 'base'

    def __init__(self, *args, **kwargs):
        pass

    @property
    def key(self):
        if not hasattr(self, '_key'):
            if not hasattr(self, 'server_name') or self.server_name == None:
                self.server_name = self.module_name()
            self._key = c.get_key(self.server_name, create_if_not_exists=True)
        return self._key
    
    @key.setter
    def key(self, key: 'Key'):
        if key == None:
            key = self.server_name
        self._key = key if hasattr(key, 'ss58_address') else c.get_key(key, create_if_not_exists=True)
        return self._key

    @classmethod
    async def async_call(cls, *args,**kwargs):
        return c.call(*args, **kwargs)
    
    def getattr(self, k:str)-> Any:
        return getattr(self,  k)

    @classmethod
    def getclassattr(cls, k:str)-> Any:
        return getattr(cls,  k)
    
    @classmethod
    def module_file(cls) -> str:
        # get the file of the module
        return inspect.getfile(cls)
    @classmethod
    def filepath(cls, obj=None) -> str:
        '''
        removes the PWD with respect to where module.py is located
        '''
        obj = cls.resolve_object(obj)
        try:
            module_path =  inspect.getfile(obj)
        except Exception as e:
            c.print(f'Error: {e} {cls}', color='red')
            module_path =  inspect.getfile(cls)
        return module_path

    pythonpath = pypath =  file_path =  filepath

    @classmethod
    def dirpath(cls) -> str:
        '''
        removes the PWD with respect to where module.py is located
        '''
        return os.path.dirname(cls.filepath())
    folderpath = dirname = dir_path =  dirpath

    @classmethod
    def module_name(cls, obj=None):
        if hasattr(cls, 'name') and isinstance(cls.name, str):
            return cls.name
        obj = cls.resolve_object(obj)
        module_file =  inspect.getfile(obj)
        return c.path2simple(module_file)
    
    path  = name = module_name 
    
    @classmethod
    def module_class(cls) -> str:
        return cls.__name__
    @classmethod
    def class_name(cls, obj= None) -> str:
        obj = obj if obj != None else cls
        return obj.__name__

    classname = class_name

    @classmethod
    def config_path(cls) -> str:
        return cls.filepath().replace('.py', '.yaml')

    @classmethod
    def sandbox(cls):
        c.cmd(f'python3 {c.root_path}/sandbox.py', verbose=True)
        return 
    
    sand = sandbox

    module_cache = {}
    _obj = None

    @classmethod
    def obj2module(cls,obj):
        import commune as c
        class WrapperModule(c.Module):
            _obj = obj
            def __name__(self):
                return obj.__name__
            def __class__(self):
                return obj.__class__
            @classmethod
            def filepath(cls) -> str:
                return super().filepath(cls._obj)  

        for fn in dir(WrapperModule):
            try:
                setattr(obj, fn, getattr(WrapperModule, fn))
            except:
                pass 
 
        return obj
    
    @classmethod
    def storage_dir(cls):
        return f'{c.cache_path}/{cls.module_name()}'
        
    @classmethod
    def refresh_storage(cls):
        cls.rm(cls.storage_dir())

    @classmethod
    def refresh_storage_dir(cls):
        c.rm(cls.storage_dir())
        c.makedirs(cls.storage_dir())
        
    ############ JSON LAND ###############

    @classmethod
    def __str__(cls):
        return cls.__name__

    @classmethod
    def root_address(cls, name:str='module',
                    network : str = 'local',
                    timeout:int = 100, 
                    sleep_interval:int = 1,
                    **kwargs):
        """
        Root module
        """
        try:
            if not c.server_exists(name, network=network):
                c.serve(name, network=network, wait_for_server=True, **kwargs)
            address = c.call('module/address', network=network, timeout=timeout)
            ip = c.ip()
            address = ip+':'+address.split(':')[-1]
        except Exception as e:
            c.print(f'Error: {e}', color='red')
            address = None
        return address
    
    addy = root_address

    @property
    def key_address(self):
        return self.key.ss58_address

    @classmethod
    def is_module(cls, obj=None) -> bool:
        
        if obj is None:
            obj = cls
        if all([hasattr(obj, k) for k in ['info', 'schema', 'set_config', 'config']]):
            return True
        return False
    
    @classmethod
    def root_functions(cls):
        return c.fns()
    
    @classmethod
    def is_root(cls, obj=None) -> bool:
        required_features = ['module_class','root_module_class', 'module_name']
        if obj is None:
            obj = cls
        if all([hasattr(obj, k) for k in required_features]):
            module_class = obj.module_class()
            if module_class == cls.root_module_class:
                return True
        return False
    is_module_root = is_root_module = is_root
    
    @classmethod
    def serialize(cls, *args, **kwargs):
        return c.module('serializer')().serialize(*args, **kwargs)
    @classmethod
    def deserialize(cls, *args, **kwargs):
        return c.module('serializer')().deserialize(*args, **kwargs)
    
    @property
    def server_name(self):
        if not hasattr(self, '_server_name'): 
            self._server_name = self.module_name()
        return self._server_name
            
    @server_name.setter
    def server_name(self, name):
        self._server_name = name

    @classmethod
    def resolve_object(cls, obj:str = None, **kwargs):
        if isinstance(obj, str):
            obj = c.module(obj, **kwargs)
        if cls._obj != None:
            return cls._obj
        else:
            return obj or cls
    
    def self_destruct(self):
        c.kill(self.server_name)    
        
    def self_restart(self):
        c.restart(self.server_name)

    @classmethod
    def pm2_start(cls, *args, **kwargs):
        return c.module('pm2').start(*args, **kwargs)
    
    @classmethod
    def pm2_launch(cls, *args, **kwargs):
        return c.module('pm2').launch(*args, **kwargs)
                              
    @classmethod
    def restart(cls, name:str, mode:str='pm2', verbose:bool = False, prefix_match:bool = True):
        refreshed_modules = getattr(cls, f'{mode}_restart')(name, verbose=verbose, prefix_match=prefix_match)
        return refreshed_modules

    def restart_self(self):
        """
        Helper function to restart the server
        """
        return c.restart(self.server_name)

    update_self = restart_self

    def kill_self(self):
        """
        Helper function to kill the server
        """
        return c.kill(self.server_name)

    refresh = reset = restart
    
    @classmethod
    def argparse(cls):
        parser = argparse.ArgumentParser(description='Argparse for the module')
        parser.add_argument('-m', '--m', '--module', '-module', dest='function', help='The function', type=str, default=cls.module_name())
        parser.add_argument('-fn', '--fn', dest='function', help='The function', type=str, default="__init__")
        parser.add_argument('-kw',  '-kwargs', '--kwargs', dest='kwargs', help='key word arguments to the function', type=str, default="{}") 
        parser.add_argument('-p', '-params', '--params', dest='params', help='key word arguments to the function', type=str, default="{}") 
        parser.add_argument('-i','-input', '--input', dest='input', help='key word arguments to the function', type=str, default="{}") 
        parser.add_argument('-args', '--args', dest='args', help='arguments to the function', type=str, default="[]")  
        args = parser.parse_args()
        args.kwargs = json.loads(args.kwargs.replace("'",'"'))
        args.params = json.loads(args.params.replace("'",'"'))
        args.inputs = json.loads(args.input.replace("'",'"'))
        args.args = json.loads(args.args.replace("'",'"'))
        args.fn = args.function
        # if you pass in the params, it will override the kwargs
        if len(args.params) > 0:
            if isinstance(args.params, dict):
                args.kwargs = args.params
            elif isinstance(args.params, list):
                args.args = args.params
            else:
                raise Exception('Invalid params', args.params)
        return args
        
    @classmethod
    def run(cls, name:str = None) -> Any: 
        is_main =  name == '__main__' or name == None or name == cls.__name__
        if not is_main:
            return {'success':False, 'message':f'Not main module {name}'}
        args = cls.argparse()
        if args.function == '__init__':
            return cls(*args.args, **args.kwargs)     
        else:
            fn = getattr(cls, args.function)
            fn_type = cls.classify_fn(fn)
            if fn_type == 'self':
                module = cls(*args.args, **args.kwargs)
            else:
                module = cls
            return getattr(module, args.function)(*args.args, **args.kwargs)     
    
    @classmethod
    def commit_hash(cls, libpath:str = None):
        if libpath == None:
            libpath = c.libpath
        return c.cmd('git rev-parse HEAD', cwd=libpath, verbose=False).split('\n')[0].strip()

    @classmethod
    def commit_ticket(cls, **kwargs):
        commit_hash = cls.commit_hash()
        ticket = c.ticket(commit_hash, **kwargs)
        assert c.verify(ticket)
        return ticket

    @classmethod
    def module_fn(cls, module:str, fn:str , args:list = None, kwargs:dict= None):
        module = c.module(module)
        is_self_method = bool(fn in module.self_functions())
        if is_self_method:
            module = module()
            fn = getattr(module, fn)
        else:
            fn =  getattr(module, fn)
        args = args or []
        kwargs = kwargs or {}
        return fn(*args, **kwargs)
    
    fn = module_fn

    @classmethod
    def info_hash(self):
        return c.commit_hash()

    @classmethod
    def module(cls,module: Any = 'module' , verbose=False, **kwargs):
        '''
        Wraps a python class as a module
        '''
        t0 = c.time()
        module_class =  c.get_module(module,**kwargs)
        latency = c.time() - t0
        c.print(f'Loaded {module} in {latency} seconds', color='green', verbose=verbose)
        return module_class
    

    _module = m = mod = module

    # UNDER CONSTRUCTION (USE WITH CAUTION)
    
    def setattr(self, k, v):
        setattr(self, k, v)

    @classmethod
    def pip_exists(cls, lib:str, verbose:str=True):
        return bool(lib in cls.pip_libs())
    
    @classmethod
    def version(cls, lib:str=libname):
        lines = [l for l in cls.cmd(f'pip3 list', verbose=False).split('\n') if l.startswith(lib)]
        if len(lines)>0:
            return lines[0].split(' ')[-1].strip()
        else:
            return f'No Library Found {lib}'

    def forward(self, a=1, b=2):
        return a+b
    
    ### DICT LAND ###

    def to_dict(self)-> Dict:
        return self.__dict__
    
    @classmethod
    def from_dict(cls, input_dict:Dict[str, Any]) -> 'Module':
        return cls(**input_dict)
        
    def to_json(self) -> str:
        state_dict = self.to_dict()
        assert isinstance(state_dict, dict), 'State dict must be a dictionary'
        assert self.jsonable(state_dict), 'State dict must be jsonable'
        return json.dumps(state_dict)
    
    @classmethod
    def from_json(cls, json_str:str) -> 'Module':
        import json
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def test_fns(cls, *args, **kwargs):
        return [f for f in cls.functions(*args, **kwargs) if f.startswith('test_')]
    
    @classmethod
    def argv(cls, include_script:bool = False):
        import sys
        args = sys.argv
        if include_script:
            return args
        else:
            return args[1:]

    @classmethod
    def is_file_module(cls, module = None) -> bool:
        if module != None:
            cls = c.module(module)
        dirpath = cls.dirpath()
        filepath = cls.filepath()
        return bool(dirpath.split('/')[-1] != filepath.split('/')[-1].split('.')[0])
    
    @classmethod
    def is_folder_module(cls,  module = None) -> bool:
        if module != None:
            cls = c.module(module)
        return not cls.is_file_module()
    
    is_module_folder = is_folder_module

    @classmethod
    def get_key(cls,key:str = None ,mode='commune', **kwargs) -> None:
        mode2module = {
            'commune': 'key',
            'subspace': 'subspace.key',
            'substrate': 'web3.account.substrate',
            'evm': 'web3.account.evm',
            'aes': 'key.aes',
            }
        
        key = cls.resolve_keypath(key)
        if 'Keypair' in c.type_str(key):
            return key
        module = c.module(mode2module[mode])
        if hasattr(module, 'get_key'):
            key = module.get_key(key, **kwargs)
        else:
            key = module(key, **kwargs)

        return key

    @classmethod
    def id(self):
        return self.key.ss58_address
    
    @property
    def ss58_address(self):
        if not hasattr(self, '_ss58_address'):
            self._ss58_address = self.key.ss58_address
        return self._ss58_address
    
    @ss58_address.setter
    def ss58_address(self, value):
        self._ss58_address = value
        return self._ss58_address

    @classmethod
    def readme_paths(cls):
        readme_paths =  [f for f in c.ls(cls.dirpath()) if f.endswith('md')]
        return readme_paths

    @classmethod
    def has_readme(cls):
        return len(cls.readme_paths()) > 0
    
    @classmethod
    def readme(cls) -> str:
        readme_paths = cls.readme_paths()
        if len(readme_paths) == 0:
            return ''
        return c.get_text(readme_paths[0])

    @classmethod
    def encrypt(cls, 
                data: Union[str, bytes],
                key: str = None, 
                password: str = None,
                **kwargs
                ) -> bytes:
        """
        encrypt data with key
        """
        key = c.get_key(key)
        return key.encrypt(data, password=password,**kwargs)

    @classmethod
    def decrypt(cls, 
                data: Union[str, bytes],
                key: str = None, 
                password : str = None,
                **kwargs) -> bytes:
        key = c.get_key(key)
        return key.decrypt(data, password=password, **kwargs)
    
    @classmethod
    def type_str(cls, x):
        return type(x).__name__
                
    @classmethod  
    def keys(cls, search = None, ss58=False,*args, **kwargs):
        if search == None:
            search = cls.module_name()
            if search == 'module':
                search = None
        keys = c.module('key').keys(search, *args, **kwargs)
        if ss58:
            keys = [c.get_key_address(k) for k in keys]
        return keys

    @classmethod  
    def get_mem(cls, *args, **kwargs):
        return c.module('key').get_mem(*args, **kwargs)
    
    mem = get_mem
    
    @classmethod
    def set_key(self, key:str, **kwargs) -> None:
        key = self.get_key(key)
        self.key = key
        return key
    
    @classmethod
    def resolve_keypath(cls, key = None):
        if key == None:
            key = cls.module_name()
        return key

    def resolve_key(self, key: str = None) -> str:
        if key == None:
            if hasattr(self, 'key'):
                key = self.key
            key = self.resolve_keypath(key)
        key = self.get_key(key)
        return key  
    
    def sign(self, data:dict  = None, key: str = None, **kwargs) -> bool:
        return self.resolve_key(key).sign(data, **kwargs)
    
    @classmethod
    def verify(cls, auth, key=None, **kwargs ) -> bool:  
        return c.get_key(key).verify(auth, **kwargs)

    @classmethod
    def verify_ticket(cls, auth, key=None, **kwargs ) -> bool:  
        return c.get_key(key).verify_ticket(auth, **kwargs)

    @classmethod
    def start(cls, *args, **kwargs):
        return cls(*args, **kwargs)
    
    def remove_user(self, key: str) -> None:
        if not hasattr(self, 'users'):
            self.users = []
        self.users.pop(key, None)
    
    @classmethod
    def is_pwd(cls, module:str = None):
        if module != None:
            module = c.module(module)
        else:
            module = cls
        return module.dirpath() == c.pwd()
    

    @classmethod
    def shortcuts(cls, cache=True) -> Dict[str, str]:
        return c.get_yaml(f'{cls.dirpath()}/shortcuts.yaml')
    
    def __repr__(self) -> str:
        return f'<{self.class_name()}'
    def __str__(self) -> str:
        return f'<{self.class_name()}'


    @classmethod
    def get_commune(cls): 
        from commune import c
        return c
    
    def pull(self):
        return c.cmd('git pull', verbose=True, cwd=c.libpath)
    
    def push(self, msg:str = 'update'):
        c.cmd('git add .', verbose=True, cwd=c.libpath)
        c.cmd(f'git commit -m "{msg}"', verbose=True, cwd=c.libpath)
        return c.cmd('git push', verbose=True, cwd=c.libpath)
    @classmethod
    def base_config(cls, cache=True):
        if cache and hasattr(cls, '_base_config'):
            return cls._base_config
        cls._base_config = cls.get_yaml(cls.config_path())
        return cls._base_config

    @classmethod
    def local_config(cls, filename_options = ['module', 'commune', 'config', 'cfg'], cache=True):
        if cache and hasattr(cls, '_local_config'):
            return cls._local_config
        local_config = {}
        for filename in filename_options:
            if os.path.exists(f'./{filename}.yaml'):
                local_config = cls.get_yaml(f'./{filename}.yaml')
            if local_config != None:
                break
        cls._local_config = local_config
        return cls._local_config
    
    @classmethod
    def local_module(cls, filename_options = ['module', 'agent', 'block'], cache=True):
        for filename in filename_options:
            path = os.path.dirname(f'./{filename}.py')
            for filename in filename_options:
                if os.path.exists(path):
                    classes = cls.find_classes(path)
                    if len(classes) > 0:
                        return classes[-1]
        return None
    
    # local update  
    @classmethod
    def update(cls, 
               module = None,
               namespace: bool = False,
               subspace: bool = False,
               network: str = 'local',
               **kwargs
               ):
        responses = []
        if module != None:
            return c.module(module).update()
        # update local namespace
        if namespace:
            responses.append(c.namespace(network=network, update=True))
        return {'success': True, 'responses': responses}

    @classmethod
    def set_key(self, key:str, **kwargs) -> None:
        key = self.get_key(key)
        self.key = key
        return key
    
    @classmethod
    def resolve_keypath(cls, key = None):
        if key == None:
            key = cls.module_name()
        return key

    def sign(self, data:dict  = None, key: str = None, **kwargs) -> bool:
        key = self.resolve_key(key)
        signature =  key.sign(data, **kwargs)
        return signature
    
    def logs(self, name:str = None, verbose: bool = False):
        return c.pm2_logs(name, verbose=verbose)
    
    def hardware(self, *args, **kwargs):
        return c.obj('commune.utils.os.hardware')(*args, **kwargs)

    def set_params(self,*args, **kwargs):
        return self.set_config(*args, **kwargs)
    
    def init_module(self,*args, **kwargs):
        return self.set_config(*args, **kwargs)
  



    helper_functions  = ['info',
                'metadata',
                'schema',
                'server_name',
                'is_admin',
                'namespace',
                'whitelist', 
                'endpoints',
                'forward',
                'module_name', 
                'class_name',
                'name',
                'address',
                'fns'] # whitelist of helper functions to load
    
    def add_endpoint(self, name, fn):
        setattr(self, name, fn)
        self.endpoints.append(name)
        assert hasattr(self, name), f'{name} not added to {self.__class__.__name__}'
        return {'success':True, 'message':f'Added {fn} to {self.__class__.__name__}'}

    def is_endpoint(self, fn) -> bool:
        if isinstance(fn, str):
            fn = getattr(self, fn)
        return hasattr(fn, '__metadata__')

    def get_endpoints(self, search: str =None , helper_fn_attributes = ['helper_functions', 
                                                                        'whitelist', 
                                                                        '_endpoints',
                                                                        '__endpoints___']):
        endpoints = []
        for k in helper_fn_attributes:
            if hasattr(self, k):
                fn_obj = getattr(self, k)
                if callable(fn_obj):
                    endpoints += fn_obj()
                else:
                    endpoints += fn_obj
        for f in dir(self):
            try:
                if not callable(getattr(self, f)) or  (search != None and search not in f):
                    continue
                fn_obj = getattr(self, f) # you need to watchout for properties
                is_endpoint = hasattr(fn_obj, '__metadata__')
                if is_endpoint:
                    endpoints.append(f)
            except Exception as e:
                print(f'Error in get_endpoints: {e} for {f}')
        return sorted(list(set(endpoints)))
    
    endpoints = get_endpoints
    

    def cost_fn(self, fn:str, args:list, kwargs:dict):
        return 1

    @classmethod
    def endpoint(cls, 
                 cost=1, # cost per call 
                 user2rate : dict = None, 
                 rate_limit : int = 100, # calls per minute
                 timestale : int = 60,
                 public:bool = False,
                 cost_keys = ['cost', 'w', 'weight'],
                 **kwargs):
        
        for k in cost_keys:
            if k in kwargs:
                cost = kwargs[k]
                break

        def decorator_fn(fn):
            metadata = {
                **cls.fn_schema(fn),
                'cost': cost,
                'rate_limit': rate_limit,
                'user2rate': user2rate,   
                'timestale': timestale,
                'public': public,            
            }
            import commune as c
            fn.__dict__['__metadata__'] = metadata

            return fn

        return decorator_fn
    


    def metadata(self, to_string=False):
        if hasattr(self, '_metadata'):
            return self._metadata
        metadata = {}
        metadata['schema'] = self.schema()
        metadata['description'] = self.description
        metadata['urls'] = {k: v for k,v in self.urls.items() if v != None}
        if to_string:
            return self.python2str(metadata)
        self._metadata =  metadata
        return metadata

    def info(self , 
             module = None,
             lite_features = ['name', 'address', 'schema', 'key', 'description'],
             lite = True,
             cost = False,
             **kwargs
             ) -> Dict[str, Any]:
        '''
        hey, whadup hey how is it going
        '''
        info = self.metadata()
        info['name'] = self.server_name or self.module_name()
        info['address'] = self.address
        info['key'] = self.key.ss58_address
        return info
    
    @classmethod
    def is_public(cls, fn):
        if not cls.is_endpoint(fn):
            return False
        return getattr(fn, '__metadata__')['public']


    urls = {'github': None,
             'website': None,
             'docs': None, 
             'twitter': None,
             'discord': None,
             'telegram': None,
             'linkedin': None,
             'email': None}
    

    
    def schema(self,
                search = None,
                docs: bool = True,
                defaults:bool = True, 
                cache=True) -> 'Schema':
        if self.is_str_fn(search):
            return self.fn_schema(search, docs=docs, defaults=defaults)
        schema = {}
        if cache and self._schema != None:
            return self._schema
        fns = self.get_endpoints()
        for fn in fns:
            if search != None and search not in fn:
                continue
            if callable(getattr(self, fn )):
                schema[fn] = self.fn_schema(fn, defaults=defaults,docs=docs)        
        # sort by keys
        schema = dict(sorted(schema.items()))
        if cache:
            self._schema = schema

        return schema

    @classmethod
    def has_routes(cls):
        return cls.config().get('routes') is not None
    
    @classmethod
    def util_functions(cls, search=None):
        utils = c.find_functions(c.root_path + '/utils')
        if search != None:
            utils = [u for u in utils if search in u]
        return utils
    
    def util_modules(self, search=None):
        return sorted(list(set([f.split('.')[-2] for f in self.util_functions(search)])))

    utils = util_functions
    @classmethod
    def util2path(cls):
        util_functions = cls.util_functions()
        util2path = {}
        for f in util_functions:
            util2path[f.split('.')[-1]] = f
        return util2path
    

    @classmethod
    def add_utils(cls, obj=None):
        obj = obj or cls
        from functools import partial
        utils = obj.util2path()
        def wrapper_fn2(fn, *args, **kwargs):
            try:
                fn = c.import_object(fn)
                return fn(*args, **kwargs)
            except : 
                fn = fn.split('.')[-1]
                return getattr(c, fn)(*args, **kwargs)
        for k, fn in utils.items():
            print(fn)
            setattr(obj, k, partial(wrapper_fn2, fn))
        return {'success': True, 'message': 'added utils'}
    route_cache = None


    @classmethod
    def routes(cls, cache=True):
        if cls.route_cache is not None and cache:
            return cls.route_cache 
        routes_path = os.path.dirname(__file__)+ '/routes.yaml'
        routes =  cls.get_yaml(routes_path)
        cls.route_cache = routes
        return routes

    #### THE FINAL TOUCH , ROUTE ALL OF THE MODULES TO THE CURRENT MODULE BASED ON THE routes CONFIG


    @classmethod
    def route_fns(cls):
        routes = cls.routes()
        route_fns = []
        for module, fns in routes.items():
            for fn in fns:
                if isinstance(fn, dict):
                    fn = fn['to']
                elif isinstance(fn, list):
                    fn = fn[1]
                elif isinstance(fn, str):
                    fn
                else:
                    raise ValueError(f'Invalid route {fn}')
                route_fns.append(fn)
        return route_fns
            

    @staticmethod
    def resolve_to_from_fn_routes(fn):
        '''
        resolve the from and to function names from the routes
        option 1: 
        {fn: 'fn_name', name: 'name_in_current_module'}
        option 2:
        {from: 'fn_name', to: 'name_in_current_module'}
        '''
        
        if type(fn) in [list, set, tuple] and len(fn) == 2:
            # option 1: ['fn_name', 'name_in_current_module']
            from_fn = fn[0]
            to_fn = fn[1]
        elif isinstance(fn, dict) and all([k in fn for k in ['fn', 'name']]):
            if 'fn' in fn and 'name' in fn:
                to_fn = fn['name']
                from_fn = fn['fn']
            elif 'from' in fn and 'to' in fn:
                from_fn = fn['from']
                to_fn = fn['to']
        else:
            from_fn = fn
            to_fn = fn
        
        return from_fn, to_fn
    

    @classmethod
    def enable_routes(cls, routes:dict=None, verbose=False):
        from functools import partial
        """
        This ties other modules into the current module.
        The way it works is that it takes the module name and the function name and creates a partial function that is bound to the module.
        This allows you to call the function as if it were a method of the current module.
        for example
        """
        my_path = cls.class_name()
        if not hasattr(cls, 'routes_enabled'): 
            cls.routes_enabled = False

        t0 = cls.time()

        # WARNING : THE PLACE HOLDERS MUST NOT INTERFERE WITH THE KWARGS OTHERWISE IT WILL CAUSE A BUG IF THE KWARGS ARE THE SAME AS THE PLACEHOLDERS
        # THE PLACEHOLDERS ARE NAMED AS module_ph and fn_ph AND WILL UNLIKELY INTERFERE WITH THE KWARGS
        def fn_generator( *args, module_ph, fn_ph, **kwargs):
            module_ph = cls.module(module_ph)
            fn_type = module_ph.classify_fn(fn_ph)
            module_ph = module_ph() if fn_type == 'self' else module_ph
            return getattr(module_ph, fn_ph)(*args, **kwargs)

        if routes == None:
            if not hasattr(cls, 'routes'):
                return {'success': False, 'msg': 'routes not found'}
            routes = cls.routes() if callable(cls.routes) else cls.routes
        for m, fns in routes.items():
            if fns in ['all', '*']:
                fns = c.functions(m)
            for fn in fns: 
                # resolve the from and to function names
                from_fn, to_fn = cls.resolve_to_from_fn_routes(fn)
                # create a partial function that is bound to the module
                fn_obj = partial(fn_generator, fn_ph=from_fn, module_ph=m )
                # make sure the funciton is as close to the original function as possible
                fn_obj.__name__ = to_fn
                # set the function to the current module
                setattr(cls, to_fn, fn_obj)
                cls.print(f'ROUTE({m}.{fn} -> {my_path}:{fn})', verbose=verbose)

        t1 = cls.time()
        cls.print(f'enabled routes in {t1-t0} seconds', verbose=verbose)
        cls.routes_enabled = True
        return {'success': True, 'msg': 'enabled routes'}
    
    @classmethod
    def fn2module(cls):
        '''
        get the module of a function
        '''
        routes = cls.routes()
        fn2module = {}
        for module, fn_routes in routes.items():
            for fn_route in fn_routes:
                if isinstance(fn_route, dict):
                    fn_route = fn_route['to']
                elif isinstance(fn_route, list):
                    fn_route = fn_route[1]
                fn2module[fn_route] = module    
        return fn2module

    def is_route(cls, fn):
        '''
        check if a function is a route
        '''
        return fn in cls.fn2module()
    

    
    @classmethod
    def has_test_module(cls, module=None):
        module = module or cls.module_name()
        return cls.module_exists(cls.module_name() + '.test')
    
    @classmethod
    def test(cls,
              module=None,
              timeout=42, 
              trials=3, 
              parallel=True,
              ):
        module = module or cls.module_name()

        if c.module_exists( module + '.test'):
            module =  module + '.test'
        print(f'testing {module}')
        module = c.module(module)()
        test_fns = module.test_fns()

        def trial_wrapper(fn, trials=trials):
            def trial_fn(trials=trials):

                for i in range(trials):
                    try:
                        return fn()
                    except Exception as e:
                        print(f'Error: {e}, Retrying {i}/{trials}')
                        cls.sleep(1)
                return False
            return trial_fn
        fn2result = {}
        if parallel:
            future2fn = {}
            for fn in test_fns:
                f = cls.submit(trial_wrapper(getattr(module, fn)), timeout=timeout)
                future2fn[f] = fn
            for f in cls.as_completed(future2fn, timeout=timeout):
                fn = future2fn.pop(f)
                fn2result[fn] = f.result()
        else:
            for fn in self.test_fns():
                print(f'testing {fn}')
                fn2result[fn] = trial_wrapper(getattr(self, fn))()       
        return fn2result
    

    @classmethod
    def add_to_globals(cls, globals_input:dict = None):
        from functools import partial
        globals_input = globals_input or {}
        for k,v in c.__dict__.items():
            globals_input[k] = v     
            
        for f in c.class_functions() + c.static_functions():
            globals_input[f] = getattr(c, f)

        for f in c.self_functions():
            def wrapper_fn(f, *args, **kwargs):
                try:
                    fn = getattr(Module(), f)
                except:
                    fn = getattr(Module, f)
                return fn(*args, **kwargs)
        
            globals_input[f] = partial(wrapper_fn, f)

        return globals_input
    


    @classmethod
    def critical(cls, *args, **kwargs):
        console = cls.resolve_console()
        return console.critical(*args, **kwargs)
    
    @classmethod
    def resolve_console(cls, console = None, **kwargs):
        if hasattr(cls,'console'):
            return cls.console
        import logging
        from rich.logging import RichHandler
        from rich.console import Console
        logging.basicConfig( handlers=[RichHandler()])   
            # print the line number
        console = Console()
        cls.console = console
        return console
    
    @classmethod
    def print(cls, *text:str, 
              color:str=None, 
              verbose:bool = True,
              console: 'Console' = None,
              flush:bool = False,
              buffer:str = None,
              **kwargs):
              
        if not verbose:
            return 
        if color == 'random':
            color = cls.random_color()
        if color:
            kwargs['style'] = color
        
        if buffer != None:
            text = [buffer] + list(text) + [buffer]

        console = cls.resolve_console(console)
        try:
            if flush:
                console.print(**kwargs, end='\r')
            console.print(*text, **kwargs)
        except Exception as e:
            print(e)
    @classmethod
    def success(cls, *args, **kwargs):
        logger = cls.resolve_logger()
        return logger.success(*args, **kwargs)

    @classmethod
    def error(cls, *args, **kwargs):
        logger = cls.resolve_logger()
        return logger.error(*args, **kwargs)
    
    @classmethod
    def debug(cls, *args, **kwargs):
        logger = cls.resolve_logger()
        return logger.debug(*args, **kwargs)
    
    @classmethod
    def warning(cls, *args, **kwargs):
        logger = cls.resolve_logger()
        return logger.warning(*args, **kwargs)
    @classmethod
    def status(cls, *args, **kwargs):
        console = cls.resolve_console()
        return console.status(*args, **kwargs)
    @classmethod
    def log(cls, *args, **kwargs):
        console = cls.resolve_console()
        return console.log(*args, **kwargs)

    ### LOGGER LAND ###
    @classmethod
    def resolve_logger(cls, logger = None):
        if not hasattr(cls,'logger'):
            from loguru import logger
            cls.logger = logger.opt(colors=True)
        if logger is not None:
            cls.logger = logger
        return cls.logger

    @staticmethod
    def echo(x):
        return x
    


    @classmethod
    def check_pid(cls, pid):        
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
    @staticmethod
    def kill_process(pid):
        import signal
        if isinstance(pid, str):
            pid = int(pid)
        
        os.kill(pid, signal.SIGKILL)

    @classmethod
    def path_exists(cls, path:str):
        return os.path.exists(path)

    @classmethod
    def ensure_path(cls, path):
        """
        ensures a dir_path exists, otherwise, it will create it 
        """

        dir_path = os.path.dirname(path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        return path


    @staticmethod
    def seed_everything(seed: int) -> None:
        import torch, random
        import numpy as np
        "seeding function for reproducibility"
        random.seed(seed)
        os.environ["PYTHONHASHSEED"] = str(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True

    @staticmethod
    def cpu_count():
        return os.cpu_count()

    num_cpus = cpu_count
    
    @staticmethod
    def get_env(key:str):
        return os.environ.get(key)
    
    @staticmethod
    def set_env(key:str, value:str):
        os.environ[key] = value
        return {'success': True, 'key': key, 'value': value}

    @staticmethod
    def get_cwd():
        return os.getcwd()
    
    @staticmethod
    def set_cwd(path:str):
        return os.chdir(path)
    

    @staticmethod
    def get_pid():
        return os.getpid()
    
    @classmethod
    def memory_usage_info(cls, fmt='gb'):
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        response = {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'pageins' : memory_info.pageins,
            'pfaults': memory_info.pfaults,
        }


        for key, value in response.items():
            response[key] = cls.format_data_size(value, fmt=fmt)

        return response



    @classmethod
    def memory_info(cls, fmt='gb'):
        import psutil

        """
        Returns the current memory usage and total memory of the system.
        """
        # Get memory statistics
        memory_stats = psutil.virtual_memory()

        # Total memory in the system
        response = {
            'total': memory_stats.total,
            'available': memory_stats.available,
            'used': memory_stats.total - memory_stats.available,
            'free': memory_stats.available,
            'active': memory_stats.active,
            'inactive': memory_stats.inactive,
            'percent': memory_stats.percent,
            'ratio': memory_stats.percent/100,
        }

        for key, value in response.items():
            if key in ['percent', 'ratio']:
                continue
            response[key] = cls.format_data_size(value, fmt=fmt)    
  
        return response

    @classmethod
    def virtual_memory_available(cls):
        import psutil
        return psutil.virtual_memory().available
    
    @classmethod
    def virtual_memory_total(cls):
        import psutil
        return psutil.virtual_memory().total
    
    @classmethod
    def virtual_memory_percent(cls):
        import psutil
        return psutil.virtual_memory().percent
    
    @classmethod
    def cpu_type(cls):
        import platform
        return platform.processor()
    
    @classmethod
    def cpu_info(cls):
        
        return {
            'cpu_count': cls.cpu_count(),
            'cpu_type': cls.cpu_type(),
        }
    

    def cpu_usage(self):
        import psutil
        # get the system performance data for the cpu
        cpu_usage = psutil.cpu_percent()
        return cpu_usage
    

    
    @classmethod
    def gpu_memory(cls):
        import torch
        return torch.cuda.memory_allocated()
    
    @classmethod
    def num_gpus(cls):
        import torch
        return torch.cuda.device_count()

    
    @classmethod
    def gpus(cls):
        return list(range(cls.num_gpus()))
    
    def add_rsa_key(cls, b=2048, t='rsa'):
        return cls.cmd(f"ssh-keygen -b {b} -t {t}")
    

    @classmethod
    def stream_output(cls, process, verbose=False):
        try:
            modes = ['stdout', 'stderr']
            for mode in modes:
                pipe = getattr(process, mode)
                if pipe == None:
                    continue
                for line in iter(pipe.readline, b''):
                    line = line.decode('utf-8')
                    if verbose:
                        cls.print(line[:-1])
                    yield line
        except Exception as e:
            print(e)
            pass

        cls.kill_process(process)

    @classmethod
    def cmd(cls, 
                    command:Union[str, list],
                    *args,
                    verbose:bool = False , 
                    env:Dict[str, str] = {}, 
                    sudo:bool = False,
                    password: bool = None,
                    bash : bool = False,
                    return_process: bool = False,
                    generator: bool =  False,
                    color : str = 'white',
                    cwd : str = None,
                    **kwargs) -> 'subprocess.Popen':
        
        '''
        Runs  a command in the shell.
        
        '''
        
        if len(args) > 0:
            command = ' '.join([command] + list(args))
        
            
        if password != None:
            sudo = True
            
        if sudo:
            command = f'sudo {command}'
            
            
        if bash:
            command = f'bash -c "{command}"'

        cwd = cls.resolve_path(cwd)
    
        env = {**os.environ, **env}

        process = subprocess.Popen(shlex.split(command),
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT,
                                    cwd = cwd,
                                    env=env, **kwargs)
        if return_process:
            return process
        streamer = cls.stream_output(process, verbose=verbose)
        if generator:
            return streamer
        else:
            text = ''
            for ch in streamer:
                text += ch
        return text

    @staticmethod
    def kill_process(process):
        import signal
        process_id = process.pid
        process.stdout.close()
        process.send_signal(signal.SIGINT)
        process.wait()
        return {'success': True, 'msg': 'process killed', 'pid': process_id}
        # sys.exit(0)

    @staticmethod
    def format_data_size(x: Union[int, float], fmt:str='b', prettify:bool=False):
        assert type(x) in [int, float, str], f'x must be int or float, not {type(x)}'
        x = float(x)
        fmt2scale = {
            'b': 1,
            'kb': 1000,
            'mb': 1000**2,
            'gb': 1000**3,
            'GiB': 1024**3,
            'tb': 1000**4,
        }
            
        assert fmt in fmt2scale.keys(), f'fmt must be one of {fmt2scale.keys()}'
        scale = fmt2scale[fmt] 
        x = x/scale 
        
        return x
    

    @classmethod
    def disk_info(cls, path:str = '/', fmt:str='gb'):
        path = cls.resolve_path(path)
        import shutil
        response = shutil.disk_usage(path)
        response = {
            'total': response.total,
            'used': response.used,
            'free': response.free,
        }
        for key, value in response.items():
            response[key] = cls.format_data_size(value, fmt=fmt)
        return response

        
    @classmethod
    def mv(cls, path1, path2):
        
        assert os.path.exists(path1), path1
        if not os.path.isdir(path2):
            path2_dirpath = os.path.dirname(path2)
            if not os.path.isdir(path2_dirpath):
                os.makedirs(path2_dirpath, exist_ok=True)
        shutil.move(path1, path2)
        assert os.path.exists(path2), path2
        assert not os.path.exists(path1), path1
        return path2

 
    @classmethod
    def cp(cls, path1:str, path2:str, refresh:bool = False):
        import shutil
        # what if its a folder?
        assert os.path.exists(path1), path1
        if refresh == False:
            assert not os.path.exists(path2), path2
        
        path2_dirpath = os.path.dirname(path2)
        if not os.path.isdir(path2_dirpath):
            os.makedirs(path2_dirpath, exist_ok=True)
            assert os.path.isdir(path2_dirpath), f'Failed to create directory {path2_dirpath}'

        if os.path.isdir(path1):
            shutil.copytree(path1, path2)


        elif os.path.isfile(path1):
            
            shutil.copy(path1, path2)
        else:
            raise ValueError(f'path1 is not a file or a folder: {path1}')
        return path2
    
    
    @classmethod
    def cuda_available(cls) -> bool:
        import torch
        return torch.cuda.is_available()

    @classmethod
    def free_gpu_memory(cls):
        gpu_info = cls.gpu_info()
        return {gpu_id: gpu_info['free'] for gpu_id, gpu_info in gpu_info.items()}

    def most_used_gpu(self):
        most_used_gpu = max(self.free_gpu_memory().items(), key=lambda x: x[1])[0]
        return most_used_gpu

    def most_used_gpu_memory(self):
        most_used_gpu = max(self.free_gpu_memory().items(), key=lambda x: x[1])[1]
        return most_used_gpu
        

    def least_used_gpu(self):
        least_used_gpu = min(self.free_gpu_memory().items(), key=lambda x: x[1])[0]
        return least_used_gpu

    def least_used_gpu_memory(self):
        least_used_gpu = min(self.free_gpu_memory().items(), key=lambda x: x[1])[1]
        return least_used_gpu
            



    @classmethod
    def gpu_info(cls, fmt='gb') -> Dict[int, Dict[str, float]]:
        import torch
        gpu_info = {}
        for gpu_id in cls.gpus():
            mem_info = torch.cuda.mem_get_info(gpu_id)
            gpu_info[int(gpu_id)] = {
                'name': torch.cuda.get_device_name(gpu_id),
                'free': mem_info[0],
                'used': (mem_info[1]- mem_info[0]),
                'total': mem_info[1], 
                'ratio': mem_info[0]/mem_info[1],
            }

        gpu_info_map = {}

        skip_keys =  ['ratio', 'total', 'name']

        for gpu_id, gpu_info in gpu_info.items():
            for key, value in gpu_info.items():
                if key in skip_keys:
                    continue
                gpu_info[key] = cls.format_data_size(value, fmt=fmt)
            gpu_info_map[gpu_id] = gpu_info
        return gpu_info_map
        

    gpu_map =gpu_info

    @classmethod
    def hardware(cls, fmt:str='gb'):
        return {
            'cpu': cls.cpu_info(),
            'memory': cls.memory_info(fmt=fmt),
            'disk': cls.disk_info(fmt=fmt),
            'gpu': cls.gpu_info(fmt=fmt),
        }

    
    @classmethod
    def get_folder_size(cls, folder_path:str='/'):
        folder_path = cls.resolve_path(folder_path)
        """Calculate the total size of all files in the folder."""
        total_size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size

    @classmethod
    def find_largest_folder(cls, directory: str = '~/'):
        directory = cls.resolve_path(directory)
        """Find the largest folder in the given directory."""
        largest_size = 0
        largest_folder = ""

        for folder_name in os.listdir(directory):
            folder_path = os.path.join(directory, folder_name)
            if os.path.isdir(folder_path):
                folder_size = cls.get_folder_size(folder_path)
                if folder_size > largest_size:
                    largest_size = folder_size
                    largest_folder = folder_path

        return largest_folder, largest_size
    

    @classmethod
    def getcwd(*args,  **kwargs):
        return os.getcwd(*args, **kwargs)
    

    @classmethod
    def argv(cls, include_script:bool = False):
        args = sys.argv
        if include_script:
            return args
        else:
            return args[1:]

    @classmethod
    def mv(cls, path1, path2):
        assert os.path.exists(path1), path1
        if not os.path.isdir(path2):
            path2_dirpath = os.path.dirname(path2)
            if not os.path.isdir(path2_dirpath):
                os.makedirs(path2_dirpath, exist_ok=True)
        shutil.move(path1, path2)
        assert os.path.exists(path2), path2
        assert not os.path.exists(path1), path1
        return {'success': True, 'msg': f'Moved {path1} to {path2}'}
    
    @classmethod
    def sys_path(cls):
        return sys.path

    @classmethod
    def gc(cls):
        gc.collect()
        return {'success': True, 'msg': 'garbage collected'}
    
    @staticmethod
    def get_pid():
        return os.getpid()
    
    @classmethod
    def nest_asyncio(cls):
        import nest_asyncio
        nest_asyncio.apply()
    
    @staticmethod
    def memory_usage(fmt='gb'):
        fmt2scale = {'b': 1e0, 'kb': 1e1, 'mb': 1e3, 'gb': 1e6}
        import psutil
        process = psutil.Process()
        scale = fmt2scale.get(fmt)
        return (process.memory_info().rss // 1024) / scale
    
    @classmethod
    def get_env(cls, key:str)-> None:
        '''
        Pay attention to this function. It sets the environment variable
        '''
        return  os.environ[key] 

    env = get_env
    
    
    def set_config(self, config:Optional[Union[str, dict]]=None ) -> 'Munch':
        '''
        Set the config as well as its local params
        '''
        # in case they passed in a locals() dict, we want to resolve the kwargs and avoid ambiguous args
        config = config or {}
        config = {**self.config(), **config}
        if isinstance(config, dict):
            config = c.dict2munch(config)
        self.config = config 
        return self.config


    
    def config_exists(self, path:str=None) -> bool:
        '''
        Returns true if the config exists
        '''
        path = path if path else self.config_path()
        return self.path_exists(path)


    @classmethod
    def config(cls) -> 'Munch':
        '''
        Returns the config
        '''
        config = cls.load_config()
        if not config:
            if hasattr(cls, 'init_kwargs'):
                config = cls.init_kwargs() # from _schema.py
            else:
                config = {}
        return config


    @classmethod
    def load_config(cls, path:str=None, 
                    default=None,
                    to_munch:bool = True  
                    ) -> Union['Munch', Dict]:
        '''
        Args:
            path: The path to the config file
            to_munch: If true, then convert the config to a munch
        '''

        default = default or {}
        path = path if path else cls.config_path()

        if os.path.exists(path):
            config = cls.load_yaml(path)
        else:
            config = default
        config = config or {} 
        if to_munch:
            config =  cls.dict2munch(config)
        return config
    
    @classmethod
    def save_config(cls, config:Union['Munch', Dict]= None, path:str=None) -> 'Munch':
        from copy import deepcopy
        from munch import Munch

        '''
        Saves the config to a yaml file
        '''
        if config == None:
            config = cls.config()
        
        if isinstance(config, Munch):
            config = cls.munch2dict(deepcopy(config))
        elif isinstance(config, dict):
            config = deepcopy(config)
        else:
            raise ValueError(f'config must be a dict or munch, not {type(config)}')
        
        assert isinstance(config, dict), f'config must be a dict, not {config}'

        config = cls.save_yaml(data=config , path=path)

        return config

    @classmethod
    def munch(cls, x:dict, recursive:bool=True)-> 'Munch':
        from munch import Munch
        '''
        Turn dictionary into Munch
        '''
        if isinstance(x, dict):
            for k,v in x.items():
                if isinstance(v, dict) and recursive:
                    x[k] = cls.dict2munch(v)
            x = Munch(x)
        return x 
    

    dict2munch = munch 

    @classmethod
    def munch2dict(cls, x:'Munch', recursive:bool=True)-> dict:
        from munch import Munch

        '''
        Turn munch object  into dictionary
        '''
        if isinstance(x, Munch):
            x = dict(x)
            for k,v in x.items():
                if isinstance(v, Munch) and recursive:
                    x[k] = cls.munch2dict(v)
        return x 
    to_dict = munch2dict
    
        
    @classmethod
    def has_config(cls) -> bool:
        
        try:
            return os.path.exists(cls.config_path())
        except:
            return False
    
    @classmethod
    def config_path(cls) -> str:
        return os.path.abspath('./config.yaml')

    def update_config(self, config):
        self.config.update(config)
        return self.config

    @classmethod
    def base_config(cls, cache=True):
        if cache and hasattr(cls, '_base_config'):
            return cls._base_config
        cls._base_config = cls.get_yaml(cls.config_path())
        return cls._base_config

    
    default_port_range = [50050, 50150] # the port range between 50050 and 50150

    @staticmethod
    def int_to_ip(int_val: int) -> str:
        r""" Maps an integer to a unique ip-string 
            Args:
                int_val  (:type:`int128`, `required`):
                    The integer representation of an ip. Must be in the range (0, 3.4028237e+38).

            Returns:
                str_val (:tyep:`str`, `required):
                    The string representation of an ip. Of form *.*.*.* for ipv4 or *::*:*:*:* for ipv6

            Raises:
                netaddr.core.AddrFormatError (Exception):
                    Raised when the passed int_vals is not a valid ip int value.
        """
        import netaddr
        return str(netaddr.IPAddress(int_val))
    
    @staticmethod
    def ip_to_int(str_val: str) -> int:
        r""" Maps an ip-string to a unique integer.
            arg:
                str_val (:tyep:`str`, `required):
                    The string representation of an ip. Of form *.*.*.* for ipv4 or *::*:*:*:* for ipv6

            Returns:
                int_val  (:type:`int128`, `required`):
                    The integer representation of an ip. Must be in the range (0, 3.4028237e+38).

            Raises:
                netaddr.core.AddrFormatError (Exception):
                    Raised when the passed str_val is not a valid ip string value.
        """
        return int(netaddr.IPAddress(str_val))

    @staticmethod
    def ip_version(str_val: str) -> int:
        r""" Returns the ip version (IPV4 or IPV6).
            arg:
                str_val (:tyep:`str`, `required):
                    The string representation of an ip. Of form *.*.*.* for ipv4 or *::*:*:*:* for ipv6

            Returns:
                int_val  (:type:`int128`, `required`):
                    The ip version (Either 4 or 6 for IPv4/IPv6)

            Raises:
                netaddr.core.AddrFormatError (Exception):
                    Raised when the passed str_val is not a valid ip string value.
        """
        return int(netaddr.IPAddress(str_val).version)

    @staticmethod
    def ip__str__(ip_type:int, ip_str:str, port:int):
        """ Return a formatted ip string
        """
        return "/ipv%i/%s:%i" % (ip_type, ip_str, port)

    @classmethod
    def is_valid_ip(cls, ip:str) -> bool:
        r""" Checks if an ip is valid.
            Args:
                ip  (:obj:`str` `required`):
                    The ip to check.

            Returns:
                valid  (:obj:`bool` `required`):
                    True if the ip is valid, False otherwise.
        """
        try:
            netaddr.IPAddress(ip)
            return True
        except Exception as e:
            return False

    @classmethod
    def external_ip(cls, default_ip='0.0.0.0') -> str:
        r""" Checks CURL/URLLIB/IPIFY/AWS for your external ip.
            Returns:
                external_ip  (:obj:`str` `required`):
                    Your routers external facing ip as a string.

            Raises:
                Exception(Exception):
                    Raised if all external ip attempts fail.
        """
        # --- Try curl.



        ip = None
        try:
            ip = cls.cmd('curl -s ifconfig.me')
            assert isinstance(cls.ip_to_int(ip), int)
        except Exception as e:
            print(e)

        if cls.is_valid_ip(ip):
            return ip
        try:
            ip = requests.get('https://api.ipify.org').text
            assert isinstance(cls.ip_to_int(ip), int)
        except Exception as e:
            print(e)

        if cls.is_valid_ip(ip):
            return ip
        # --- Try AWS
        try:
            ip = requests.get('https://checkip.amazonaws.com').text.strip()
            assert isinstance(cls.ip_to_int(ip), int)
        except Exception as e:
            print(e)

        if cls.is_valid_ip(ip):
            return ip
        # --- Try myip.dnsomatic 
        try:
            process = os.popen('curl -s myip.dnsomatic.com')
            ip  = process.readline()
            assert isinstance(cls.ip_to_int(ip), int)
            process.close()
        except Exception as e:
            print(e)  

        if cls.is_valid_ip(ip):
            return ip
        # --- Try urllib ipv6 
        try:
            ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
            assert isinstance(cls.ip_to_int(ip), int)
        except Exception as e:
            print(e)

        if cls.is_valid_ip(ip):
            return ip
        # --- Try Wikipedia 
        try:
            ip = requests.get('https://www.wikipedia.org').headers['X-Client-IP']
            assert isinstance(cls.ip_to_int(ip), int)
        except Exception as e:
            print(e)

        if cls.is_valid_ip(ip):
            return ip

        return default_ip
    
    @classmethod
    def unreserve_port(cls,port:int, 
                       var_path='reserved_ports'):
        reserved_ports =  cls.get(var_path, {}, root=True)
        
        port_info = reserved_ports.pop(port,None)
        if port_info == None:
            port_info = reserved_ports.pop(str(port),None)
        
        output = {}
        if port_info != None:
            cls.put(var_path, reserved_ports, root=True)
            output['msg'] = 'port removed'
        else:
            output['msg'] =  f'port {port} doesnt exist, so your good'

        output['reserved'] =  cls.reserved_ports()
        return output
    
    

    
    @classmethod
    def unreserve_ports(cls,*ports, 
                       var_path='reserved_ports' ):
        reserved_ports =  cls.get(var_path, {})
        if len(ports) == 0:
            # if zero then do all fam, tehe
            ports = list(reserved_ports.keys())
        elif len(ports) == 1 and isinstance(ports[0],list):
            ports = ports[0]
        ports = list(map(str, ports))
        reserved_ports = {rp:v for rp,v in reserved_ports.items() if not any([p in ports for p in [str(rp), int(rp)]] )}
        cls.put(var_path, reserved_ports)
        return cls.reserved_ports()
    
    
    @classmethod
    def check_used_ports(cls, start_port = 8501, end_port = 8600, timeout=5):
        port_range = [start_port, end_port]
        used_ports = {}
        for port in range(*port_range):
            used_ports[port] = cls.port_used(port)
        return used_ports
    

    @classmethod
    def kill_port(cls, port:int):
        r""" Kills a process running on the passed port.
            Args:
                port  (:obj:`int` `required`):
                    The port to kill the process on.
        """
        try:
            os.system(f'kill -9 $(lsof -t -i:{port})')
        except Exception as e:
            print(e)
            return False
        return True
    
    def kill_ports(self, ports = None, *more_ports):
        ports = ports or self.used_ports()
        if isinstance(ports, int):
            ports = [ports]
        if '-' in ports:
            ports = list(range([int(p) for p in ports.split('-')]))
        ports = list(ports) + list(more_ports)
        for port in ports:
            self.kill_port(port)
        return self.check_used_ports()
    
    def public_ports(self, timeout=1.0):
        import commune as c
        futures = []
        for port in self.free_ports():
            c.print(f'Checking port {port}')
            futures += [c.submit(self.is_port_open, {'port':port}, timeout=timeout)]
        results =  c.wait(futures, timeout=timeout)
        results = list(map(bool, results))
        return results
    


    def is_port_open(self, port:int, ip:str=None, timeout=0.5):
        import commune as c
        ip = ip or self.ip()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((ip, port)) == 0
        return False
            


    @classmethod
    def free_ports(cls, n=10, random_selection:bool = False, **kwargs ) -> List[int]:
        free_ports = []
        avoid_ports = kwargs.pop('avoid_ports', [])
        for i in range(n):
            try:
                free_ports += [cls.free_port(  random_selection=random_selection, 
                                            avoid_ports=avoid_ports, **kwargs)]
            except Exception as e:
                cls.print(f'Error: {e}', color='red')
                break
            avoid_ports += [free_ports[-1]]
        
              
        return free_ports
    
    @classmethod
    def random_port(cls, *args, **kwargs):
        return cls.choice(cls.free_ports(*args, **kwargs))
    

    

    @classmethod
    def free_port(cls, 
                  ports = None,
                  port_range: List[int] = None , 
                  ip:str =None, 
                  avoid_ports = None,
                  random_selection:bool = True) -> int:
        
        '''
        
        Get an availabldefe port within the {port_range} [start_port, end_poort] and {ip}
        '''
        avoid_ports = avoid_ports if avoid_ports else []
        
        if ports == None:
            port_range = cls.get_port_range(port_range)
            ports = list(range(*port_range))
            
        ip = ip if ip else cls.default_ip

        if random_selection:
            ports = cls.shuffle(ports)
        port = None
        for port in ports: 
            if port in avoid_ports:
                continue
            
            if cls.port_available(port=port, ip=ip):
                return port
            
        raise Exception(f'ports {port_range[0]} to {port_range[1]} are occupied, change the port_range to encompase more ports')

    get_available_port = free_port



    def check_used_ports(self, start_port = 8501, end_port = 8600, timeout=5):
        port_range = [start_port, end_port]
        used_ports = {}
        for port in range(*port_range):
            used_ports[port] = self.port_used(port)
        return used_ports
    


    @classmethod
    def resolve_port(cls, port:int=None, **kwargs):
        
        '''
        
        Resolves the port and finds one that is available
        '''
        if port == None or port == 0:
            port = cls.free_port(port, **kwargs)
            
        if cls.port_used(port):
            port = cls.free_port(port, **kwargs)
            
        return int(port)

   

    @classmethod
    def port_available(cls, port:int, ip:str ='0.0.0.0'):
        return not cls.port_used(port=port, ip=ip)
        

    @classmethod
    def port_used(cls, port: int, ip: str = '0.0.0.0', timeout: int = 1):
        import socket
        if not isinstance(port, int):
            return False
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Set the socket timeout
            sock.settimeout(timeout)

            # Try to connect to the specified IP and port
            try:
                port=int(port)
                sock.connect((ip, port))
                return True
            except socket.error:
                return False
    
    @classmethod
    def port_free(cls, *args, **kwargs) -> bool:
        return not cls.port_used(*args, **kwargs)

    @classmethod
    def port_available(cls, port:int, ip:str ='0.0.0.0'):
        return not cls.port_used(port=port, ip=ip)
    
        

    @classmethod
    def used_ports(cls, ports:List[int] = None, ip:str = '0.0.0.0', port_range:Tuple[int, int] = None):
        '''
        Get availabel ports out of port range
        
        Args:
            ports: list of ports
            ip: ip address
        
        '''
        port_range = cls.resolve_port_range(port_range=port_range)
        if ports == None:
            ports = list(range(*port_range))
        
        async def check_port(port, ip):
            return cls.port_used(port=port, ip=ip)
        
        used_ports = []
        jobs = []
        for port in ports: 
            jobs += [check_port(port=port, ip=ip)]
                
        results = cls.wait(jobs)
        for port, result in zip(ports, results):
            if isinstance(result, bool) and result:
                used_ports += [port]
            
        return used_ports
    
    @classmethod
    def scan_ports(cls,host=None, start_port=None, end_port=None, timeout=24):
        if start_port == None and end_port == None:
            start_port, end_port = cls.port_range()
        if host == None:
            host = cls.external_ip()
        import socket
        open_ports = []
        future2port = {}
        for port in range(start_port, end_port + 1):  # ports from start_port to end_port
            future2port[cls.submit(cls.port_used, kwargs=dict(port=port, ip=host), timeout=timeout)] = port
        port2open = {}
        for future in cls.as_completed(future2port, timeout=timeout):
            port = future2port[future]
            port2open[port] = future.result()
        # sort the ports
        port2open = {k: v for k, v in sorted(port2open.items(), key=lambda item: item[1])}

        return port2open

    @classmethod
    def resolve_port(cls, port:int=None, **kwargs):
        '''
        Resolves the port and finds one that is available
        '''
        if port == None or port == 0:
            port = cls.free_port(port, **kwargs)
        if cls.port_used(port):
            port = cls.free_port(port, **kwargs)
        return int(port)

    @classmethod
    def has_free_ports(self, n:int = 1, **kwargs):
        return len(self.free_ports(n=n, **kwargs)) > 0
    

    @classmethod
    def get_port_range(cls, port_range: list = None) -> list:
        port_range = cls.get('port_range', cls.default_port_range)
        if isinstance(port_range, str):
            port_range = list(map(int, port_range.split('-')))
        if len(port_range) == 0:
            port_range = cls.default_port_range
        port_range = list(port_range)
        assert isinstance(port_range, list), 'Port range must be a list'
        assert isinstance(port_range[0], int), 'Port range must be a list of integers'
        assert isinstance(port_range[1], int), 'Port range must be a list of integers'
        return port_range
    
    @classmethod
    def port_range(cls):
        return cls.get_port_range()
    
    @classmethod
    def resolve_port_range(cls, port_range: list = None) -> list:
        return cls.get_port_range(port_range)

    @classmethod
    def set_port_range(cls, *port_range: list):
        if '-' in port_range[0]:
            port_range = list(map(int, port_range[0].split('-')))
        if len(port_range) ==0 :
            port_range = cls.default_port_range
        elif len(port_range) == 1:
            if port_range[0] == None:
                port_range = cls.default_port_range
        assert len(port_range) == 2, 'Port range must be a list of two integers'        
        for port in port_range:
            assert isinstance(port, int), f'Port {port} range must be a list of integers'
        assert port_range[0] < port_range[1], 'Port range must be a list of integers'
        cls.put('port_range', port_range)
        return port_range
    
    @classmethod
    def get_port(cls, port:int = None)->int:
        port = port if port is not None and port != 0 else cls.free_port()
        while cls.port_used(port):
            port += 1   
        return port 
    
    @classmethod
    def port_free(cls, *args, **kwargs) -> bool:
        return not cls.port_used(*args, **kwargs)

    @classmethod
    def port_available(cls, port:int, ip:str ='0.0.0.0'):
        return not cls.port_used(port=port, ip=ip)
        
    @classmethod
    def used_ports(cls, ports:List[int] = None, ip:str = '0.0.0.0', port_range:Tuple[int, int] = None):
        '''
        Get availabel ports out of port range
        
        Args:
            ports: list of ports
            ip: ip address
        
        '''
        port_range = cls.resolve_port_range(port_range=port_range)
        if ports == None:
            ports = list(range(*port_range))
        
        async def check_port(port, ip):
            return cls.port_used(port=port, ip=ip)
        
        used_ports = []
        jobs = []
        for port in ports: 
            jobs += [check_port(port=port, ip=ip)]
                
        results = cls.gather(jobs)
        for port, result in zip(ports, results):
            if isinstance(result, bool) and result:
                used_ports += [port]
            
        return used_ports
    

    get_used_ports = used_ports
    
    @classmethod
    def get_available_ports(cls, port_range: List[int] = None , ip:str =None) -> int:
        port_range = cls.resolve_port_range(port_range)
        ip = ip if ip else cls.default_ip
        
        available_ports = []
        # return only when the port is available
        for port in range(*port_range): 
            if not cls.port_used(port=port, ip=ip):
                available_ports.append(port)
                  
        return available_ports
    available_ports = get_available_ports

    @classmethod
    def set_ip(cls, ip):
        
        cls.put('ip', ip)
        return ip
    
    @classmethod
    def ip(cls,  max_age=None, update:bool = False, **kwargs) -> str:
        ip = cls.get('ip', None, max_age=max_age, update=update)
        if ip == None:
            ip =  cls.external_ip(**kwargs)
            cls.put('ip', ip)
        return ip

    @classmethod
    def resolve_address(cls, address:str = None):
        if address == None:
            address = c.free_address()
        assert isinstance(address, str),  'address must be a string'
        return address

    @classmethod
    def free_address(cls, **kwargs):
        return f'{cls.ip()}:{cls.free_port(**kwargs)}'

    @classmethod
    def check_used_ports(cls, start_port = 8501, end_port = 8600, timeout=5):
        port_range = [start_port, end_port]
        used_ports = {}
        for port in range(*port_range):
            used_ports[port] = cls.port_used(port)
        return used_ports
    
    @classmethod
    def resolve_ip(cls, ip=None, external:bool=True) -> str:
        if ip == None:
            if external:
                ip = cls.external_ip()
            else:
                ip = '0.0.0.0'
        assert isinstance(ip, str)
        return ip
    

    @classmethod
    def put_json(cls, 
                 path:str, 
                 data:Dict, 
                 meta = None,
                 verbose: bool = False,
                 **kwargs) -> str:
        if meta != None:
            data = {'data':data, 'meta':meta}
        path = cls.resolve_path(path=path, extension='json')
        # cls.lock_file(path)
        if isinstance(data, dict):
            data = json.dumps(data)
        cls.put_text(path, data)
        return path
    
    save_json = put_json

    @classmethod
    def rm_json(cls, path=None):
        from commune.utils.dict import rm_json
        if path in ['all', '**']:
            return [cls.rm_json(f) for f in cls.glob(files_only=False)]
        path = cls.resolve_path(path=path, extension='json')
        return rm_json(path )
    
    @classmethod
    def rmdir(cls, path):
        return shutil.rmtree(path)

    @classmethod
    def isdir(cls, path):
        path = cls.resolve_path(path=path)
        return os.path.isdir(path)
        
    @classmethod
    def isfile(cls, path):
        path = cls.resolve_path(path=path)
        return os.path.isfile(path)
    
    @classmethod
    def rm_all(cls):
        for path in cls.ls():
            cls.rm(path)
        return {'success':True, 'message':f'{cls.storage_dir()} removed'}
        
    @classmethod
    def rm(cls, path, extension=None, mode = 'json'):
        
        assert isinstance(path, str), f'path must be a string, got {type(path)}'
        path = cls.resolve_path(path=path, extension=extension)

        # incase we want to remove the json file
        mode_suffix = f'.{mode}'
        if not os.path.exists(path) and os.path.exists(path+mode_suffix):
            path += mode_suffix

        if not os.path.exists(path):
            return {'success':False, 'message':f'{path} does not exist'}
        if os.path.isdir(path):
            cls.rmdir(path)
        if os.path.isfile(path):
            os.remove(path)
        assert not os.path.exists(path), f'{path} was not removed'

        return {'success':True, 'message':f'{path} removed'}
    
    @classmethod
    def rm_all(cls):
        storage_dir = cls.storage_dir()
        if cls.exists(storage_dir):
            cls.rm(storage_dir)
        assert not cls.exists(storage_dir), f'{storage_dir} was not removed'
        cls.makedirs(storage_dir)
        assert cls.is_dir_empty(storage_dir), f'{storage_dir} was not removed'
        return {'success':True, 'message':f'{storage_dir} removed'}



    @classmethod
    def rm_all(cls):
        storage_dir = cls.storage_dir()
        if cls.exists(storage_dir):
            cls.rm(storage_dir)
        assert not cls.exists(storage_dir), f'{storage_dir} was not removed'
        cls.makedirs(storage_dir)
        assert cls.is_dir_empty(storage_dir), f'{storage_dir} was not removed'
        return {'success':True, 'message':f'{storage_dir} removed'}


    @classmethod
    def glob(cls,  path =None, files_only:bool = True, recursive:bool=True):
        import glob
        path = cls.resolve_path(path, extension=None)
        if os.path.isdir(path):
            path = os.path.join(path, '**')
        paths = glob.glob(path, recursive=recursive)
        if files_only:
            paths =  list(filter(lambda f:os.path.isfile(f), paths))
        return paths
    

    @classmethod
    def put_cache(cls,k,v ):
        cls.cache[k] = v
    
    @classmethod
    def get_cache(cls,k, default=None, **kwargs):
        v = cls.cache.get(k, default)
        return v


    @classmethod
    def get_json(cls, 
                path:str,
                default:Any=None,
                verbose: bool = False,**kwargs):
        path = cls.resolve_path(path=path, extension='json')

        cls.print(f'Loading json from {path}', verbose=verbose)

        try:
            data = cls.get_text(path, **kwargs)
        except Exception as e:
            return default
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                return default
        if isinstance(data, dict):
            if 'data' in data and 'meta' in data:
                data = data['data']
        return data
    @classmethod
    async def async_get_json(cls,*args, **kwargs):
        return  cls.get_json(*args, **kwargs)

    load_json = get_json


    @classmethod
    def file_exists(cls, path:str)-> bool:
        path = cls.resolve_path(path)
        exists =  os.path.exists(path)
        return exists

 
    exists = exists_json = file_exists


    @classmethod
    def makedirs(cls, *args, **kwargs):
        return os.makedirs(*args, **kwargs)


    @classmethod
    def mv(cls, path1, path2):
        path1 = cls.resolve_path(path1)
        path2 = cls.resolve_path(path2)
        assert os.path.exists(path1), path1
        if not os.path.isdir(path2):
            path2_dirpath = os.path.dirname(path2)
            if not os.path.isdir(path2_dirpath):
                os.makedirs(path2_dirpath, exist_ok=True)
        shutil.move(path1, path2)
        assert os.path.exists(path2), path2
        assert not os.path.exists(path1), path1
        return path2

    @classmethod
    def resolve_path(cls, path:str = None, extension=None):
        '''
        ### Documentation for `resolve_path` class method
        
        #### Purpose:
        The `resolve_path` method is a class method designed to process and resolve file and directory paths based on various inputs and conditions. This method is useful for preparing file paths for operations such as reading, writing, and manipulation.
        
        #### Parameters:
        - `path` (str, optional): The initial path to be resolved. If not provided, a temporary directory path will be returned.
        - `extension` (Optional[str], optional): The file extension to append to the path if necessary. Defaults to None.
        - `root` (bool, optional): A flag to determine whether the path should be resolved in relation to the root directory. Defaults to False.
        - `file_type` (str, optional): The default file type/extension to append if the `path` does not exist but appending the file type results in a valid path. Defaults to 'json'.
        
        #### Behavior:
        - If `path` is not provided, the method returns a path to a temporary directory.
        - If `path` starts with '/', it is returned as is.
        - If `path` starts with '~/', it is expanded to the user’s home directory.
        - If `path` starts with './', it is resolved to an absolute path.
        - If `path` does not fall under the above conditions, it is treated as a relative path. If `root` is True, it is resolved relative to the root temp directory; otherwise, relative to the class's temp directory.
        - If `path` is a relative path and does not contain the temp directory, the method joins `path` with the appropriate temp directory.
        - If `path` does not exist as a directory and an `extension` is provided, the extension is appended to `path`.
        - If `path` does not exist but appending the `file_type` results in an existing path, the `file_type` is appended.
        - The parent directory of `path` is created if it does not exist, avoiding any errors when the path is accessed later.
        
        #### Returns:
        - `str`: The resolved and potentially created path, ensuring it is ready for further file operations. 
        
        #### Example Usage:
        ```python
        # Resolve a path in relation to the class's temporary directory
        file_path = MyClassName.resolve_path('data/subfolder/file', extension='txt')
        
        # Resolve a path in relation to the root temporary directory
        root_file_path = MyClassName.resolve_path('configs/settings'
        ```
        
        #### Notes:
        - This method relies on the `os` module to perform path manipulations and checks.
        - This method is versatile and can handle various input path formats, simplifying file path resolution in the class's context.
        '''
    
        if path == None:
            return cls.storage_dir()
        
        if path.startswith('/'):
            path = path
        elif path.startswith('~'):
            path =  os.path.expanduser(path)
        elif path.startswith('.'):
            path = os.path.abspath(path)
        else:
            # if it is a relative path, then it is relative to the module path
            # ex: 'data' -> '.commune/path_module/data'
            storage_dir = cls.storage_dir()
            if storage_dir not in path:
                path = os.path.join(storage_dir, path)

        if extension != None and not path.endswith(extension):
            path = path + '.' + extension

        return path
    


    @staticmethod
    def ensure_path( path):
        """
        ensures a dir_path exists, otherwise, it will create it 
        """

        dir_path = os.path.dirname(path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        return path

    @staticmethod
    async def async_write(path, data,  mode ='w'):
        import aiofiles
        async with aiofiles.open(path, mode=mode) as f:
            await f.write(data)
            
    @classmethod
    def put_yaml(cls, path:str,  data: dict) -> Dict:
        from munch import Munch
        from copy import deepcopy
        '''
        Loads a yaml file
        '''
        # Directly from dictionary
        data_type = type(data)
        if data_type in [pd.DataFrame]:
            data = data.to_dict()
        if data_type in [Munch]:
            data = cls.munch2dict(deepcopy(data))
        if data_type in [dict, list, tuple, set, float, str, int]:
            yaml_str = yaml.dump(data)
        else:
            raise NotImplementedError(f"{data_type}, is not supported")
        with open(path, 'w') as file:
            file.write(yaml_str)
        return {'success': True, 'msg': f'Wrote yaml to {path}'}
        

        
    

    @classmethod
    def get_yaml(cls, path:str=None, default={}, **kwargs) -> Dict:
        '''f
        Loads a yaml file
        '''
        path = cls.resolve_path(path)
        with open(path, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        return data
    
        
    load_yaml = get_yaml

    save_yaml = put_yaml 
    
    @classmethod
    def filesize(cls, filepath:str):
        filepath = cls.resolve_path(filepath)
        return os.path.getsize(filepath)
    

    def search_files(self, path:str='./', search:str='__pycache__') -> List[str]:
        path = self.resolve_path(path)
        files = self.glob(path)
        return list(filter(lambda x: search in x, files))
    
    def rm_pycache(self, path:str='./') -> List[str]:
        files = self.search_files(path, search='__pycache__')
        for file in files:
            self.print(self.rm(file))
        return files
    
    def file2size(self, path='./', fmt='mb') -> int:
        files = self.glob(path)
        file2size = {}
        pwd = self.pwd()
        for file in files:
            file2size[file.replace(pwd+'/','')] = self.format_data_size(self.filesize(file), fmt)

        # sort by size
        file2size = dict(sorted(file2size.items(), key=lambda item: item[1]))
        return file2size


    @classmethod
    def cp(cls, path1:str, path2:str, refresh:bool = False):
        # what if its a folder?
        assert os.path.exists(path1), path1
        if refresh == False:
            assert not os.path.exists(path2), path2
        
        path2_dirpath = os.path.dirname(path2)
        if not os.path.isdir(path2_dirpath):
            os.makedirs(path2_dirpath, exist_ok=True)
            assert os.path.isdir(path2_dirpath), f'Failed to create directory {path2_dirpath}'

        if os.path.isdir(path1):
            shutil.copytree(path1, path2)


        elif os.path.isfile(path1):
            
            shutil.copy(path1, path2)
        else:
            raise ValueError(f'path1 is not a file or a folder: {path1}')
        return {'success': True, 'msg': f'Copied {path1} to {path2}'}

    @classmethod
    def put_text(cls, path:str, text:str, key=None, bits_per_character=8) -> None:
        # Get the absolute path of the file
        path = cls.resolve_path(path)
        dirpath = os.path.dirname(path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        if not isinstance(text, str):
            text = cls.python2str(text)
        if key != None:
            text = cls.get_key(key).encrypt(text)
        # Write the text to the file
        with open(path, 'w') as file:
            file.write(text)
        # get size
        text_size = len(text)*bits_per_character
    
        return {'success': True, 'msg': f'Wrote text to {path}', 'size': text_size}
    
    @classmethod
    def lsdir(cls, path:str) -> List[str]:
        path = os.path.abspath(path)
        return os.listdir(path)

    @classmethod
    def abspath(cls, path:str) -> str:
        return os.path.abspath(path)


    @classmethod
    def ls(cls, path:str = '', 
           recursive:bool = False,
           search = None,
           return_full_path:bool = True):
        """
        provides a list of files in the path 

        this path is relative to the module path if you dont specifcy ./ or ~/ or /
        which means its based on the module path
        """
        path = cls.resolve_path(path)
        try:
            ls_files = cls.lsdir(path) if not recursive else cls.walk(path)
        except FileNotFoundError:
            return []
        if return_full_path:
            ls_files = [os.path.abspath(os.path.join(path,f)) for f in ls_files]

        ls_files = sorted(ls_files)
        if search != None:
            ls_files = list(filter(lambda x: search in x, ls_files))
        return ls_files
    


    @classmethod
    def put(cls, 
            k: str, 
            v: Any,  
            mode: bool = 'json',
            encrypt: bool = False, 
            verbose: bool = False, 
            password: str = None, **kwargs) -> Any:
        '''
        Puts a value in the config
        '''
        encrypt = encrypt or password != None
        
        if encrypt or password != None:
            v = cls.encrypt(v, password=password)

        if not cls.jsonable(v):
            v = cls.serialize(v)    
        
        data = {'data': v, 'encrypted': encrypt, 'timestamp': cls.timestamp()}            
        
        # default json 
        getattr(cls,f'put_{mode}')(k, data)

        data_size = cls.sizeof(v)
    
        return {'k': k, 'data_size': data_size, 'encrypted': encrypt, 'timestamp': cls.timestamp()}
    
    @classmethod
    def get(cls,
            k:str, 
            default: Any=None, 
            mode:str = 'json',
            max_age:str = None,
            cache :bool = False,
            full :bool = False,
            key: 'Key' = None,
            update :bool = False,
            password : str = None,
            verbose = True,
            **kwargs) -> Any:
        
        '''
        Puts a value in sthe config, with the option to encrypt it

        Return the value
        '''
        if cache:
            if k in cls.cache:
                return cls.cache[k]
        data = getattr(cls, f'get_{mode}')(k,default=default, **kwargs)
        

        if password != None:
            assert data['encrypted'] , f'{k} is not encrypted'
            data['data'] = cls.decrypt(data['data'], password=password, key=key)

        data = data or default
        
        if isinstance(data, dict):
            if update:
                max_age = 0
            if max_age != None:
                timestamp = data.get('timestamp', None)
                if timestamp != None:
                    age = int(time.time() - timestamp)
                    if age > max_age: # if the age is greater than the max age
                        cls.print(f'{k} is too old ({age} > {max_age})', verbose=verbose)
                        return default
        else:
            data = default
            
        if not full:
            if isinstance(data, dict):
                if 'data' in data:
                    data = data['data']

        # local cache
        if cache:
            cls.cache[k] = data
        return data
    
    def get_age(self, k:str) -> int:
        data = self.get_json(k)
        timestamp = data.get('timestamp', None)
        if timestamp != None:
            age = int(time.time() - timestamp)
            return age
        return -1
    
    @classmethod
    def get_text(cls, 
                 path: str, 
                 tail = None,
                 start_byte:int = 0,
                 end_byte:int = 0,
                 start_line :int= None,
                 end_line:int = None ) -> str:
        # Get the absolute path of the file
        path = cls.resolve_path(path)

        if not os.path.exists(path):
            if os.path.exists(path + '.json'):
                path = path + '.json'

        # Read the contents of the file
        with open(path, 'rb') as file:

            file.seek(0, 2) # this is done to get the fiel size
            file_size = file.tell()  # Get the file size
            if start_byte < 0:
                start_byte = file_size - start_byte
            if end_byte <= 0:
                end_byte = file_size - end_byte 
            if end_byte < start_byte:
                end_byte = start_byte + 100
            chunk_size = end_byte - start_byte + 1

            file.seek(start_byte)

            content_bytes = file.read(chunk_size)

            # Convert the bytes to a string
            try:
                content = content_bytes.decode()
            except UnicodeDecodeError as e:
                if hasattr(content_bytes, 'hex'):
                    content = content_bytes.hex()
                else:
                    raise e

            if tail != None:
                content = content.split('\n')
                content = '\n'.join(content[-tail:])
    
            elif start_line != None or end_line != None:
                
                content = content.split('\n')
                if end_line == None or end_line == 0 :
                    end_line = len(content) 
                if start_line == None:
                    start_line = 0
                if start_line < 0:
                    start_line = start_line + len(content)
                if end_line < 0 :
                    end_line = end_line + len(content)
                content = '\n'.join(content[start_line:end_line])
            else:
                content = content_bytes.decode()
        return content


    def is_encrypted(self, path:str) -> bool:
        try:
            return self.get_json(path).get('encrypted', False)
        except:
            return False

    @classmethod
    def storage_dir(cls):
        return f'{cls.cache_path}/{cls.module_name()}'
    
    tmp_dir = cache_dir   = storage_dir
    
    @classmethod
    def refresh_storage(cls):
        cls.rm(cls.storage_dir())

    @classmethod
    def refresh_storage_dir(cls):
        cls.rm(cls.storage_dir())
        cls.makedirs(cls.storage_dir())
        

    @classmethod
    def rm_lines(cls, path:str, start_line:int, end_line:int) -> None:
        # Get the absolute path of the file
        text = cls.get_text(path)
        text = text.split('\n')
        text = text[:start_line-1] + text[end_line:]
        text = '\n'.join(text)
        cls.put_text(path, text)
        return {'success': True, 'msg': f'Removed lines {start_line} to {end_line} from {path}'}
    @classmethod
    def rm_line(cls, path:str, line:int, text=None) -> None:
        # Get the absolute path of the file
        text =  cls.get_text(path)
        text = text.split('\n')
        text = text[:line-1] + text[line:]
        text = '\n'.join(text)
        cls.put_text(path, text)
        return {'success': True, 'msg': f'Removed line {line} from {path}'}
        # Write the text to the file
            
    @classmethod
    def tilde_path(cls):
        return os.path.expanduser('~')

    def is_dir_empty(self, path:str):
        return len(self.ls(path)) == 0
    
    @classmethod
    def get_file_size(cls, path:str):
        path = cls.resolve_path(path)
        return os.path.getsize(path)

    @staticmethod
    def jsonable( value):
        import json
        try:
            json.dumps(value)
            return True
        except:
            return False

    def file2text(self, path = './', relative=True,  **kwargs):
        path = os.path.abspath(path)
        file2text = {}
        for file in c.glob(path, recursive=True):
            with open(file, 'r') as f:
                content = f.read()
                file2text[file] = content
        if relative:
            print(path)
            return {k[len(path)+1:]:v for k,v in file2text.items()}

        return file2text
    
    def file2lines(self, path:str='./')-> List[str]:
        file2text = self.file2text(path)
        file2lines = {f: text.split('\n') for f, text in file2text.items()}
        return file2lines
    
    def num_files(self, path:str='./')-> int:
        import commune as c
        return len(c.glob(path))
    
    def hidden_files(self, path:str='./')-> List[str]:
        import commune as c
        path = self.resolve_path(path)
        files = [f[len(path)+1:] for f in  c.glob(path)]
        print(files)
        hidden_files = [f for f in files if f.startswith('.')]
        return hidden_files
    
    @staticmethod
    def format_data_size(x: Union[int, float], fmt:str='b', prettify:bool=False):
        assert type(x) in [int, float], f'x must be int or float, not {type(x)}'
        fmt2scale = {
            'b': 1,
            'kb': 1000,
            'mb': 1000**2,
            'gb': 1000**3,
            'GiB': 1024**3,
            'tb': 1000**4,
        }
            
        assert fmt in fmt2scale.keys(), f'fmt must be one of {fmt2scale.keys()}'
        scale = fmt2scale[fmt] 
        x = x/scale 
        
        if prettify:
            return f'{x:.2f} {f}'
        else:
            return x

    @classmethod
    def get_schema(cls,
                module = None,
                search = None,
                whitelist = None,
                fn = None,
                docs: bool = True,
                include_parents:bool = False,
                defaults:bool = True, cache=False) -> 'Schema':
        
        if '/' in str(search):
            module, fn = search.split('/')
            cls = cls.module(module)
        if isinstance(module, str):
            if '/' in module:
                module , fn = module.split('/')
            module = cls.module(module)
        module = module or cls
        schema = {}
        fns = module.get_functions()
        for fn in fns:
            if search != None and search not in fn:
                continue
            if callable(getattr(module, fn )):
                schema[fn] = cls.fn_schema(fn, defaults=defaults,docs=docs)        
        # sort by keys
        schema = dict(sorted(schema.items()))
        if whitelist != None :
            schema = {k:v for k,v in schema.items() if k in whitelist}
        return schema
    
        
    @classmethod
    def determine_type(cls, x):
        if x.lower() == 'null' or x == 'None':
            return None
        elif x.lower() in ['true', 'false']:
            return bool(x.lower() == 'true')
        elif x.startswith('[') and x.endswith(']'):
            # this is a list
            try:
                
                list_items = x[1:-1].split(',')
                # try to convert each item to its actual type
                x =  [cls.determine_type(item.strip()) for item in list_items]
                if len(x) == 1 and x[0] == '':
                    x = []
                return x
       
            except:
                # if conversion fails, return as string
                return x
        elif x.startswith('{') and x.endswith('}'):
            # this is a dictionary
            if len(x) == 2:
                return {}
            try:
                dict_items = x[1:-1].split(',')
                # try to convert each item to a key-value pair
                return {key.strip(): cls.determine_type(value.strip()) for key, value in [item.split(':', 1) for item in dict_items]}
            except:
                # if conversion fails, return as string
                return x
        else:
            # try to convert to int or float, otherwise return as string
            try:
                return int(x)
            except ValueError:
                try:
                    return float(x)
                except ValueError:
                    return x
                
    
    @classmethod
    def fn2code(cls, search=None, module=None)-> Dict[str, str]:
        module = module if module else cls
        functions = module.fns(search)
        fn_code_map = {}
        for fn in functions:
            try:
                fn_code_map[fn] = module.fn_code(fn)
            except Exception as e:
                print(f'Error: {e}')
        return fn_code_map
    

    
    @classmethod
    def fn_code(cls,fn:str, 
                detail:bool=False, 
                seperator: str = '/'
                ) -> str:
        '''
        Returns the code of a function
        '''
        try:
            fn = cls.get_fn(fn)
            code_text = inspect.getsource(fn)
            text_lines = code_text.split('\n')
            if 'classmethod' in text_lines[0] or 'staticmethod' in text_lines[0] or '@' in text_lines[0]:
                text_lines.pop(0)
            fn_code = '\n'.join([l[len('    '):] for l in code_text.split('\n')])
            assert 'def' in text_lines[0], 'Function not found in code'

            if detail:
                start_line = cls.find_code_line(search=text_lines[0])
                fn_code =  {
                    'text': fn_code,
                    'start_line': start_line ,
                    'end_line':  start_line + len(text_lines)
                }
        except Exception as e:
            print(f'Error: {e}')
            fn_code = None
                    
        return fn_code
    

    @classmethod
    def fn_hash(cls,fn:str = 'subspace/ls', detail:bool=False,  seperator: str = '/') -> str:
            
        fn_code = cls.fn_code(fn, detail=detail, seperator=seperator)
        return cls.hash(fn_code)

    @classmethod
    def is_generator(cls, obj):
        """
        Is this shiz a generator dawg?
        """
        if isinstance(obj, str):
            if not hasattr(cls, obj):
                return False
            obj = getattr(cls, obj)
        if not callable(obj):
            result = inspect.isgenerator(obj)
        else:
            result =  inspect.isgeneratorfunction(obj)
        return result
    @classmethod
    def get_parents(cls, obj = None,recursive=True, avoid_classes=['object']) -> List[str]:
        obj = cls.resolve_object(obj)
        parents =  list(obj.__bases__)
        if recursive:
            for parent in parents:
                parent_parents = cls.get_parents(parent, recursive=recursive)
                if len(parent_parents) > 0:
                    for pp in parent_parents: 
                        if pp.__name__ not in avoid_classes:
                        
                            parents += [pp]
        return parents


    @classmethod
    def get_class_name(cls, obj = None) -> str:
        obj = cls or obj
        if not cls.is_class(obj):
            obj = type(obj)
        return obj.__name__
    

    @classmethod
    def fn_signature_map(cls, obj=None, include_parents:bool = False):
        obj = cls.resolve_object(obj)
        function_signature_map = {}
        for f in cls.get_functions(obj = obj, include_parents=include_parents):
            if f.startswith('__') and f.endswith('__'):
                if f in ['__init__']:
                    pass
                else:
                    continue
            if not hasattr(cls, f):
                continue
            if callable(getattr(cls, f )):
                function_signature_map[f] = {k:str(v) for k,v in cls.get_function_signature(getattr(cls, f )).items()}        
        return function_signature_map


    @classmethod
    def fn_schema(cls, fn:str,
                            defaults:bool=True,
                            code:bool = False,
                            docs:bool = True, **kwargs)->dict:
        '''
        Get function schema of function in cls
        '''
        fn_schema = {}
        fn = cls.get_fn(fn)
        input_schema  = cls.fn_signature(fn)
        for k,v in input_schema.items():
            v = str(v)
            if v.startswith('<class'):
                input_schema[k] = v.split("'")[1]
            elif v.startswith('typing.'):
                input_schema[k] = v.split(".")[1].lower()
            else:
                input_schema[k] = v

        fn_schema['input'] = input_schema
        fn_schema['output'] = input_schema.pop('return', {})

        if docs:         
            fn_schema['docs'] =  fn.__doc__ 
        if code:
            fn_schema['code'] = cls.fn_code(fn)

        fn_args = cls.get_function_args(fn)
        fn_schema['type'] = 'static'
        for arg in fn_args:
            if arg not in fn_schema['input']:
                fn_schema['input'][arg] = 'NA'
            if arg in ['self', 'cls']:
                fn_schema['type'] = arg
                fn_schema['input'].pop(arg)

        if defaults:
            fn_defaults = cls.fn_defaults(fn=fn) 
            for k,v in fn_defaults.items(): 
                if k not in fn_schema['input'] and v != None:
                    fn_schema['input'][k] = type(v).__name__ if v != None else None

        fn_schema['input'] = {k: {'type':v, 'default':fn_defaults.get(k)} for k,v in fn_schema['input'].items()}

        return fn_schema
    
    @classmethod
    def fn_info(cls, fn:str='test_fn') -> dict:
        r = {}
        code = cls.fn_code(fn)
        lines = code.split('\n')
        mode = 'self'
        if '@classmethod' in lines[0]:
            mode = 'class'
        elif '@staticmethod' in lines[0]:
            mode = 'static'
    
        start_line_text = 0
        lines_before_fn_def = 0
        for l in lines:
            
            if f'def {fn}('.replace(' ', '') in l.replace(' ', ''):
                start_line_text = l
                break
            else:
                lines_before_fn_def += 1
            
        assert start_line_text != None, f'Could not find function {fn} in {cls.pypath()}'
        module_code = cls.code()
        start_line = cls.find_code_line(start_line_text, code=module_code) - 1

        end_line = start_line + len(lines)   # find the endline
        has_docs = bool('"""' in code or "'''" in code)
        filepath = cls.filepath()

        # start code line
        for i, line in enumerate(lines):
            
            is_end = bool(')' in line and ':' in line)
            if is_end:
                start_code_line = i
                break 

        
        return {
            'start_line': start_line,
            'end_line': end_line,
            'has_docs': has_docs,
            'code': code,
            'n_lines': len(lines),
            'hash': cls.hash(code),
            'path': filepath,
            'start_code_line': start_code_line + start_line ,
            'mode': mode
            
        }
    


    @classmethod
    def find_code_line(cls, search:str=None, code:str = None):
        if code == None:
            code = cls.code() # get the code
        found_lines = [] # list of found lines
        for i, line in enumerate(code.split('\n')):
            if str(search) in line:
                found_lines.append({'idx': i+1, 'text': line})
        if len(found_lines) == 0:
            return None
        elif len(found_lines) == 1:
            return found_lines[0]['idx']
        return found_lines
    


    @classmethod
    def attributes(cls):
        return list(cls.__dict__.keys())


    @classmethod
    def get_attributes(cls, search = None, obj=None):
        if obj is None:
            obj = cls
        if isinstance(obj, str):
            obj = c.module(obj)
        # assert hasattr(obj, '__dict__'), f'{obj} has no __dict__'
        attrs =  dir(obj)
        if search is not None:
            attrs = [a for a in attrs if search in a and callable(a)]
        return attrs
    

    
    def add_fn(self, fn, name=None):
        if name == None:
            name = fn.__name__
        assert not hasattr(self, name), f'{name} already exists'

        setattr(self, name, fn)

        return {
            'success':True ,
            'message':f'Added {name} to {self.__class__.__name__}'
        }
    

    add_attribute = add_attr = add_function = add_fn

    @classmethod
    def init_schema(cls):
        return cls.fn_schema('__init__')
    


    @classmethod
    def init_kwargs(cls):
        kwargs =  cls.fn_defaults('__init__')
        kwargs.pop('self', None)
        if 'config' in kwargs:
            if kwargs['config'] != None:
                kwargs.update(kwargs.pop('config'))
            del kwargs['config']
        if 'kwargs' in kwargs:
            if kwargs['kwargs'] != None:
                kwargs = kwargs.pop('kwargs')
            del kwargs['kwargs']

        return kwargs
    init_params = init_kwargs
    
    @classmethod
    def lines_of_code(cls, code:str=None):
        if code == None:
            code = cls.code()
        return len(code.split('\n'))

    @classmethod
    def code(cls, module = None, search=None, *args, **kwargs):
        if '/' in str(module) or module in cls.fns():
            return cls.fn_code(module)
        module = cls.resolve_object(module)
        print(module)
        text =  cls.get_text( module.filepath(), *args, **kwargs)
        if search != None:
            find_lines = cls.find_lines(text=text, search=search)
            return find_lines
        return text
    pycode = code
    @classmethod
    def chash(cls,  *args, **kwargs):
        import commune as c
        """
        The hash of the code, where the code is the code of the class (cls)
        """
        code = cls.code(*args, **kwargs)
        return c.hash(code)
    
    @classmethod
    def find_code_line(cls, search:str, code:str = None):
        if code == None:
            code = cls.code() # get the code
        found_lines = [] # list of found lines
        for i, line in enumerate(code.split('\n')):
            if search in line:
                found_lines.append({'idx': i+1, 'text': line})
        if len(found_lines) == 0:
            return None
        elif len(found_lines) == 1:
            return found_lines[0]['idx']
        return found_lines
    

    def fn_code_first_line(self, fn):
        code = self.fn_code(fn)
        return code.split('):')[0] + '):'
    
    def fn_code_first_line_idx(self, fn):
        code = self.fn_code(fn)
        return self.find_code_line(self.fn_code_first_line(fn), code=code)
    
    
    @classmethod
    def fn_info(cls, fn:str='test_fn') -> dict:
        r = {}
        code = cls.fn_code(fn)
        lines = code.split('\n')
        mode = 'self'
        if '@classmethod' in lines[0]:
            mode = 'class'
        elif '@staticmethod' in lines[0]:
            mode = 'static'
        module_code = cls.code()
        in_fn = False
        start_line = 0
        end_line = 0
        fn_code_lines = []
        for i, line in enumerate(module_code.split('\n')):
            if f'def {fn}('.replace(' ', '') in line.replace(' ', ''):
                in_fn = True
                start_line = i + 1
            if in_fn:
                fn_code_lines.append(line)
                if ('def ' in line or '' == line) and len(fn_code_lines) > 1:
                    end_line = i - 1
                    break

        if not in_fn:
            end_line = start_line + len(fn_code_lines)   # find the endline
        # start code line
        for i, line in enumerate(lines):
            
            is_end = bool(')' in line and ':' in line)
            if is_end:
                start_code_line = i
                break 

        return {
            'start_line': start_line,
            'end_line': end_line,
            'code': code,
            'n_lines': len(lines),
            'hash': cls.hash(code),
            'start_code_line': start_code_line + start_line ,
            'mode': mode
            
        }
    

    @classmethod
    def set_line(cls, idx:int, text:str):
        code = cls.code()
        lines = code.split('\n')
        if '\n' in text:
            front_lines = lines[:idx]
            back_lines = lines[idx:]
            new_lines = text.split('\n')
            lines = front_lines + new_lines + back_lines
        else:
            lines[idx-1] = text
        new_code = '\n'.join(lines)
        cls.put_text(cls.filepath(), new_code)
        return {'success': True, 'msg': f'Set line {idx} to {text}'}

    @classmethod
    def add_line(cls, idx=0, text:str = '',  module=None  ):
        """
        add line to an index of the module code
        """

        code = cls.code() if module == None else c.module(module).code()
        lines = code.split('\n')
        new_lines = text.split('\n') if '\n' in text else [text]
        lines = lines[:idx] + new_lines + lines[idx:]
        new_code = '\n'.join(lines)
        cls.put_text(cls.filepath(), new_code)
        return {'success': True, 'msg': f'Added line {idx} to {text}'}

    @classmethod
    def get_line(cls, idx):
        code = cls.code()
        lines = code.split('\n')
        assert idx < len(lines), f'idx {idx} is out of range for {len(lines)}'  
        line =  lines[max(idx, 0)]
        print(len(line))
        return line
    
    @classmethod
    def fn_defaults(cls, fn):
        """
        Gets the function defaults
        """
        fn = cls.get_fn(fn)
        function_defaults = dict(inspect.signature(fn)._parameters)
        for k,v in function_defaults.items():
            if v._default != inspect._empty and  v._default != None:
                function_defaults[k] = v._default
            else:
                function_defaults[k] = None

        return function_defaults
 
    @staticmethod
    def is_class(obj):
        '''
        is the object a class
        '''
        return type(obj).__name__ == 'type'


    @classmethod
    def resolve_class(cls, obj):
        '''
        resolve class of object or return class if it is a class
        '''
        if cls.is_class(obj):
            return obj
        else:
            return obj.__class__
        


    @classmethod
    def has_var_keyword(cls, fn='__init__', fn_signature=None):
        if fn_signature == None:
            fn_signature = cls.resolve_fn(fn)
        for param_info in fn_signature.values():
            if param_info.kind._name_ == 'VAR_KEYWORD':
                return True
        return False
    
    @classmethod
    def fn_signature(cls, fn) -> dict: 
        '''
        get the signature of a function
        '''
        if isinstance(fn, str):
            fn = getattr(cls, fn)
        return dict(inspect.signature(fn)._parameters)
    
    get_function_signature = fn_signature
    @classmethod
    def is_arg_key_valid(cls, key='config', fn='__init__'):
        fn_signature = cls.fn_signature(fn)
        if key in fn_signature: 
            return True
        else:
            for param_info in fn_signature.values():
                if param_info.kind._name_ == 'VAR_KEYWORD':
                    return True
        
        return False
    

    
    @classmethod
    def self_functions(cls: Union[str, type], obj=None, search=None):
        '''
        Gets the self methods in a class
        '''
        obj = cls.resolve_object(obj)
        functions =  cls.get_functions(obj)
        signature_map = {f:cls.get_function_args(getattr(obj, f)) for f in functions}
        if search != None:
            functions = [f for f in functions if search in f]
        return [k for k, v in signature_map.items() if 'self' in v]
    
    @classmethod
    def class_functions(cls: Union[str, type], obj=None):
        '''
        Gets the self methods in a class
        '''
        obj = cls.resolve_object(obj)
        functions =  cls.get_functions(obj)
        signature_map = {f:cls.get_function_args(getattr(obj, f)) for f in functions}
        return [k for k, v in signature_map.items() if 'cls' in v]
    
    class_methods = get_class_methods =  class_fns = class_functions

    @classmethod
    def static_functions(cls: Union[str, type], obj=None):
        '''
        Gets the self methods in a class
        '''
        obj = obj or cls
        functions =  cls.get_functions(obj)
        signature_map = {f:cls.get_function_args(getattr(obj, f)) for f in functions}
        return [k for k, v in signature_map.items() if not ('self' in v or 'cls' in v)]
    
    static_methods = static_fns =  static_functions

    @classmethod
    def property_fns(cls) -> bool:
        '''
        Get a list of property functions in a class
        '''
        return [fn for fn in dir(cls) if cls.is_property(fn)]
    
    parents = get_parents
    
    @classmethod
    def parent2functions(cls, obj=None):
        '''
        Get the parent classes of a class
        '''
        obj = cls.resolve_object(obj)
        parent_functions = {}
        for parent in cls.parents(obj):
            parent_functions[parent.__name__] = cls.get_functions(parent)
        return parent_functions
    
    parent2fns = parent2functions

    @classmethod
    def get_functions(cls, obj: Any = None,
                      search = None,
                      include_parents:bool=True, 
                      include_hidden:bool = False) -> List[str]:
        '''
        Get a list of functions in a class
        
        Args;
            obj: the class to get the functions from
            include_parents: whether to include the parent functions
            include_hidden:  whether to include hidden functions (starts and begins with "__")
        '''
        is_root_module = cls.is_root_module()
        obj = cls.resolve_object(obj)
        if include_parents:
            parent_functions = cls.parent_functions(obj)
        else:
            parent_functions = []
        avoid_functions = []
        if not is_root_module:
            import commune as c
            avoid_functions = c.functions()
        else:
            avoid_functions = []

        functions = []
        child_functions = dir(obj)
        function_names = [fn_name for fn_name in child_functions + parent_functions]

        for fn_name in function_names:
            if fn_name in avoid_functions:
                continue
            if not include_hidden:
                if ((fn_name.startswith('__') or fn_name.endswith('_'))):
                    if fn_name != '__init__':
                        continue
            fn_obj = getattr(obj, fn_name)
            # if the function is callable, include it
            if callable(fn_obj):
                functions.append(fn_name)

        text_derived_fns = cls.parse_functions_from_module_text()
    
        functions = sorted(list(set(functions + text_derived_fns)))
            
        if search != None:
            functions = [f for f in functions if search in f]
        return functions
    
    @classmethod
    def functions(cls, search = None, include_parents = True):
        return cls.get_functions(search=search, include_parents=include_parents)


    @classmethod
    def get_conflict_functions(cls, obj = None):
        '''
        Does the object conflict with the current object
        '''
        if isinstance(obj, str):
            obj = cls.get_module(obj)
        root_fns = cls.root_functions()
        conflict_functions = []
        for fn in obj.functions():
            if fn in root_fns:
                print(f'Conflict: {fn}')
                conflict_functions.append(fn)
        return conflict_functions
    
    @classmethod
    def does_module_conflict(cls, obj):
        return len(cls.get_conflict_functions(obj)) > 0
    

    
    @classmethod
    def parse_functions_from_module_text(cls, obj=None, splitter_options = ["   def " , "    def "]):
        # reutrn only functions in this class
        import inspect
        obj = obj or cls
        text = inspect.getsource(obj)
        functions = []
        for splitter in splitter_options:
            for line in text.split('\n'):
                if f'"{splitter}"' in line:
                    continue
                if line.startswith(splitter):
                    functions += [line.split(splitter)[1].split('(')[0]]

        return functions


    def n_fns(self, search = None):
        return len(self.fns(search=search))
    
    fn_n = n_fns
    @classmethod
    def fns(self, search = None, include_parents = True):
        return self.get_functions(search=search, include_parents=include_parents)
    @classmethod
    def is_property(cls, fn: 'Callable') -> bool:
        '''
        is the function a property
        '''
        try:
            fn = cls.get_fn(fn, ignore_module_pattern=True)
        except :
            return False

        return isinstance(fn, property)

    def is_fn_self(self, fn):
        fn = self.resolve_fn(fn)
        return hasattr(fn, '__self__') and fn.__self__ == self



    @classmethod
    def get_fn(cls, fn:str, init_kwargs = None):
        """
        Gets the function from a string or if its an attribute 
        """
        if isinstance(fn, str):
            is_object = cls.object_exists(fn)
            if is_object:
                return cls.get_object(fn)
            elif '/' in fn:
                module, fn = fn.split('/')
                cls = cls.get_module(module)
            try:
                fn =  getattr(cls, fn)
            except:
                init_kwargs = init_kwargs or {}
                fn = getattr(cls(**init_kwargs), fn)

        if callable(fn) or isinstance(fn, property):
            pass

        return fn
        
    @classmethod
    def self_functions(cls, search = None):
        fns =  cls.classify_fns(cls)['self']
        if search != None:
            fns = [f for f in fns if search in f]
        return fns
    

    @classmethod
    def classify_fns(cls, obj= None, mode=None):
        method_type_map = {}
        obj = cls.resolve_object(obj)
        for attr_name in dir(obj):
            method_type = None
            try:
                method_type = cls.classify_fn(getattr(obj, attr_name))
            except Exception as e:
                continue
        
            if method_type not in method_type_map:
                method_type_map[method_type] = []
            method_type_map[method_type].append(attr_name)
        if mode != None:
            method_type_map = method_type_map[mode]
        return method_type_map


    @classmethod
    def get_args(cls, fn) -> List[str]:
        """
        get the arguments of a function
        params:
            fn: the function
        
        """
        # if fn is an object get the __
        
        if not callable(fn):
            fn = cls.get_fn(fn)
        try:
            args = inspect.getfullargspec(fn).args
        except Exception as e:
            args = []
        return args
    
    get_function_args = get_args 

    
    @classmethod
    def has_function_arg(cls, fn, arg:str):
        args = cls.get_function_args(fn)
        return arg in args

    
    fn_args = get_fn_args =  get_function_args
    
    @classmethod
    def classify_fn(cls, fn):
        try:
            if not callable(fn):
                fn = cls.get_fn(fn)
            if not callable(fn):
                return 'cls'
            args = cls.get_function_args(fn)
            if args[0] == 'self':
                return 'self'
            elif args[0] == 'cls':
                return 'class'
        except Exception as e:
            return 'property'
        return 'static'
        
    

    @classmethod
    def python2types(cls, d:dict)-> dict:
        return {k:str(type(v)).split("'")[1] for k,v in d.items()}
    



    @classmethod
    def fn2str(cls,search = None,  code = True, defaults = True, **kwargs):
        fns = cls.fns(search=search)
        fn2str = {}
        for fn in fns:
            fn2str[fn] = cls.fn_code(fn)
            
        return fn2str
    @classmethod
    def fn2hash(cls, fn=None , mode='sha256', **kwargs):
        fn2hash = {}
        for k,v in cls.fn2str(**kwargs).items():
            fn2hash[k] = c.hash(v,mode=mode)
        if fn:
            return fn2hash[fn]
        return fn2hash

    # TAG CITY     
    @classmethod
    def parent_functions(cls, obj = None, include_root = True):
        functions = []
        obj = obj or cls
        parents = cls.get_parents(obj)
        for parent in parents:
            is_parent_root = cls.is_root_module(parent)
            if is_parent_root:
                continue
            
            for name, member in parent.__dict__.items():
                if not name.startswith('__'):
                    functions.append(name)
        return functions

    @classmethod
    def child_functions(cls, obj=None):
        obj = cls.resolve_object(obj)
        
        methods = []
        for name, member in obj.__dict__.items():
            if inspect.isfunction(member) and not name.startswith('__'):
                methods.append(name)
        
        return methods

    @classmethod
    def locals2kwargs(cls,locals_dict:dict, kwargs_keys=['kwargs']) -> dict:
        locals_dict = locals_dict or {}
        kwargs = locals_dict or {}
        kwargs.pop('cls', None)
        kwargs.pop('self', None)

        assert isinstance(kwargs, dict), f'kwargs must be a dict, got {type(kwargs)}'
        
        # These lines are needed to remove the self and cls from the locals_dict
        for k in kwargs_keys:
            kwargs.update( locals_dict.pop(k, {}) or {})

        return kwargs



    

    def kwargs2attributes(self, kwargs:dict, ignore_error:bool = False):
        for k,v in kwargs.items():
            if k != 'self': # skip the self
                # we dont want to overwrite existing variables from 
                if not ignore_error: 
                    assert not hasattr(self, k)
                setattr(self, k)

    def num_fns(self):
        return len(self.fns())

    
    def fn2type(self):
        fn2type = {}
        fns = self.fns()
        for f in fns:
            if callable(getattr(self, f)):
                fn2type[f] = self.classify_fn(getattr(self, f))
        return fn2type
    

    @classmethod
    def is_dir_module(cls, path:str) -> bool:
        """
        determine if the path is a module
        """
        filepath = cls.simple2path(path)
        if path.replace('.', '/') + '/' in filepath:
            return True
        if ('modules/' + path.replace('.', '/')) in filepath:
            return True
        return False
    
    @classmethod
    def add_line(cls, path:str, text:str, line=None) -> None:
        # Get the absolute path of the file
        path = cls.resolve_path(path)
        text = str(text)
        # Write the text to the file
        if line != None:
            line=int(line)
            lines = cls.get_text(path).split('\n')
            lines = lines[:line] + [text] + lines[line:]

            text = '\n'.join(lines)
        with open(path, 'w') as file:
            file.write(text)


        return {'success': True, 'msg': f'Added line to {path}'}


    @classmethod
    def readme(cls):
        # Markdown input
        markdown_text = "## Hello, *Markdown*!"
        path = cls.filepath().replace('.py', '_docs.md')
        markdown_text =  cls.get_text(path=path)
        return markdown_text
    
    docs = readme


    @staticmethod
    def is_imported(package:str) :
        return  bool(package in sys.modules)
    
    @classmethod
    def is_parent(cls, obj=None):
        obj = obj or cls 
        return bool(obj in cls.get_parents())

    @classmethod
    def find_code_lines(cls,  search:str = None , module=None) -> List[str]:
        module_code = cls.get_module(module).code()
        return cls.find_lines(search=search, text=module_code)

    @classmethod
    def find_lines(self, text:str, search:str) -> List[str]:
        """
        Finds the lines in text with search
        """
        found_lines = []
        lines = text.split('\n')
        for line in lines:
            if search in line:
                found_lines += [line]
        
        return found_lines
    

    @classmethod
    def params(cls, fn='__init__'):
        params =  cls.fn_defaults(fn)
        params.pop('self', None)
        return params
    
    
    @classmethod
    def is_str_fn(cls, fn):
        if fn == None:
            return False
        if '/' in fn:
            module, fn = fn.split('/')
            module = cls.module(module)
        else:
            module = cls 
        
        return hasattr(module, fn)
        


    @classmethod
    def resolve_extension(cls, filename:str, extension = '.py') -> str:
        if filename.endswith(extension):
             return filename
        return filename + extension

    @classmethod
    def simple2path(cls, 
                    simple:str,
                    extension = '.py',
                    avoid_dirnames = ['', 'src', 
                                      'commune', 
                                      'commune/module', 
                                      'commune/modules', 
                                      'modules', 
                                      'blocks', 
                                      'agents', 
                                      'commune/agents'],
                    **kwargs) -> bool:
        """
        converts the module path to a file path

        for example 

        model.openai.gpt3 -> model/openai/gpt3.py, model/openai/gpt3_module.py, model/openai/__init__.py 
        model.openai -> model/openai.py or model/openai_module.py or model/__init__.py

        Parameters:
            path (str): The module path
        """
        # if cls.libname in simple and '/' not in simple and cls.can_import_module(simple):
        #     return simple
        shortcuts = cls.shortcuts()
        simple = shortcuts.get(simple, simple)

        if simple.endswith(extension):
            simple = simple[:-len(extension)]

        path = None
        pwd = cls.pwd()
        path_options = []
        simple = simple.replace('/', '.')

        # create all of the possible paths by combining the avoid_dirnames with the simple path
        dir_paths = list([pwd+ '/' + x for x in avoid_dirnames]) # local first
        dir_paths += list([cls.libpath + '/' + x for x in avoid_dirnames]) # add libpath stuff

        for dir_path in dir_paths:
            if dir_path.endswith('/'):
                dir_path = dir_path[:-1]
            # '/' count how many times the path has been split
            module_dirpath = dir_path + '/' + simple.replace('.', '/')
            if os.path.isdir(module_dirpath):
                simple_filename = simple.replace('.', '_')
                filename_options = [simple_filename, simple_filename + '_module', 'module_'+ simple_filename] + ['module'] + simple.split('.') + ['__init__']
                path_options +=  [module_dirpath + '/' + f  for f in filename_options]  
            else:
                module_filepath = dir_path + '/' + simple.replace('.', '/') 
                path_options += [module_filepath]
            for p in path_options:
                p = cls.resolve_extension(p)
                if os.path.exists(p):
                    p_text = cls.get_text(p)
                    path =  p
                    if 'commune' in p_text and 'class ' in p_text or '  def ' in p_text:
                        return p   
            if path != None:
                break
        return path

    
    @classmethod
    def is_repo(cls, libpath:str ):
        # has the .git folder
        return bool([f for f in cls.ls(libpath) if '.git' in f and os.path.isdir(f)])

    
    @classmethod
    def path2simple(cls,  
                    path:str, 
                    tree = None,  
                    ignore_prefixes = ['src', 'commune', 'modules', 'commune.modules',
                                       'commune.commune',
                                        'commune.module', 'module', 'router'],
                    module_folder_filnames = ['__init__', 'main', 'module'],
                    module_extension = 'py',
                    ignore_suffixes = ['module'],
                    name_map = {'commune': 'module'},
                    compress_path = True,
                    verbose = False,
                    num_lines_to_read = 100,
                    ) -> str:
        
        path  = os.path.abspath(path)
        path_filename_with_extension = path.split('/')[-1] # get the filename with extension     
        path_extension = path_filename_with_extension.split('.')[-1] # get the extension
        assert path_extension == module_extension, f'Invalid extension {path_extension} for path {path}'
        path_filename = path_filename_with_extension[:-len(path_extension)-1] # remove the extension
        path_filename_chunks = path_filename.split('_')
        path_chunks = path.split('/')

        if path.startswith(cls.libpath):
            path = path[len(cls.libpath):]
        else:
            # if the tree path is not in the path, we want to remove the root path
            pwd = cls.pwd()
            path = path[len(pwd):] 
        dir_chunks = path.split('/')[:-1] if '/' in path else []
        is_module_folder = all([bool(chunk in dir_chunks) for chunk in path_filename_chunks])
        is_module_folder = is_module_folder or (path_filename in module_folder_filnames)
        if is_module_folder:
            path = '/'.join(path.split('/')[:-1])
        path = path[1:] if path.startswith('/') else path
        path = path.replace('/', '.')
        module_extension = '.'+module_extension
        if path.endswith(module_extension):
            path = path[:-len(module_extension)]
        if compress_path:
            # we want to remove redundant chunks 
            # for example if the path is 'module/module' we want to remove the redundant module
            path_chunks = path.split('.')
            simple_path = []
            for chunk in path_chunks:
                if chunk not in simple_path:
                    simple_path += [chunk]
            simple_path = '.'.join(simple_path)
        else:
            simple_path = path
        # FILTER PREFIXES  
        for prefix in ignore_prefixes:
            prefix += '.'
            if simple_path.startswith(prefix) and simple_path != prefix:
                simple_path = simple_path[len(prefix):]
                cls.print(f'Prefix {prefix} in path {simple_path}', color='yellow', verbose=verbose)
        # FILTER SUFFIXES
        for suffix in ignore_suffixes:
            suffix = '.' + suffix
            if simple_path.endswith(suffix) and simple_path != suffix:
                simple_path = simple_path[:-len(suffix)]
                cls.print(f'Suffix {suffix} in path {simple_path}', color='yellow', verbose=verbose)

        # remove leading and trailing dots
        if simple_path.startswith('.'):
            simple_path = simple_path[1:]
        if simple_path.endswith('.'):
            simple_path = simple_path[:-1]
        simple_path = name_map.get(simple_path, simple_path)
        return simple_path

    @classmethod
    def path_config_exists(cls, path:str,
                            config_files = ['config.yaml', 'config.yml'],
                              config_extensions=['.yaml', '.yml']) -> bool:
        '''
        Checks if the path exists
        '''
        config_files += [path.replace('.py', ext) for ext in config_extensions]
        dirpath = os.path.dirname(path)
        dir_files =  os.listdir(dirpath)
        if os.path.exists(dirpath) and any([[f.endswith(cf) for cf in config_files] for f in dir_files]):
            return True
        return False


    @classmethod
    def resolve_cache_path(self, path):
        path = path.replace("/", "_")
        if path.startswith('_'):
            path = path[1:]
        path = f'cached_path/{path}'
        return path
    
    @classmethod
    def cached_paths(cls):
        return cls.ls('cached_paths')
    

    @classmethod
    def find_classes(cls, path='./',  working=False):

        path = os.path.abspath(path)
        if os.path.isdir(path):
            classes = []
            generator = cls.glob(path+'/**/**.py', recursive=True)
            for p in generator:
                if p.endswith('.py'):
                    p_classes =  cls.find_classes(p )
                    if working:
                        for class_path in p_classes:
                            try:
                                cls.import_object(class_path)
                                classes += [class_path]
                            except Exception as e:
                                r = cls.detailed_error(e)
                                r['class'] = class_path
                                cls.print(r, color='red')
                                continue
                    else:
                        classes += p_classes
                        
            return classes
        
        code = cls.get_text(path)
        classes = []
        file_path = cls.path2objectpath(path)
            
        for line in code.split('\n'):
            if all([s in line for s in ['class ', ':']]):
                new_class = line.split('class ')[-1].split('(')[0].strip()
                if new_class.endswith(':'):
                    new_class = new_class[:-1]
                if ' ' in new_class:
                    continue
                classes += [new_class]
        classes = [file_path + '.' + c for c in classes]

        libpath_objpath_prefix = cls.libpath.replace('/', '.')[1:] + '.'
        classes = [c.replace(libpath_objpath_prefix, '') for c in classes]
        return classes
    



    @classmethod
    def find_class2functions(cls, path,  working=False):

        path = os.path.abspath(path)
        if os.path.isdir(path):
            class2functions = {}
            for p in cls.glob(path+'/**/**.py', recursive=True):
                if p.endswith('.py'):
                    object_path = cls.path2objectpath(p)
                    response =  cls.find_class2functions(p )
                    for k,v in response.items():
                        class2functions[object_path+ '.' +k] = v
            return class2functions

        code = cls.get_text(path)
        classes = []
        class2functions = {}
        class_functions = []
        new_class = None
        for line in code.split('\n'):
            if all([s in line for s in ['class ', ':']]):
                new_class = line.split('class ')[-1].split('(')[0].strip()
                if new_class.endswith(':'):
                    new_class = new_class[:-1]
                if ' ' in new_class:
                    continue
                classes += [new_class]
                if len(class_functions) > 0:
                    class2functions[new_class] = cls.copy(class_functions)
                class_functions = []
            if all([s in line for s in ['   def', '(']]):
                fn = line.split(' def')[-1].split('(')[0].strip()
                class_functions += [fn]
        if new_class != None:
            class2functions[new_class] = class_functions

        return class2functions
    
    @classmethod
    def path2objectpath(cls, path:str, **kwargs) -> str:
        libpath = cls.libpath 
        if path.startswith(libpath):
            path =   path.replace(libpath , '')[1:].replace('/', '.').replace('.py', '')
        else: 
            pwd = cls.pwd()
            if path.startswith(pwd):
                path =  path.replace(pwd, '')[1:].replace('/', '.').replace('.py', '')
            
        return path.replace('__init__.', '.')
    
    @classmethod
    def objecpath2path(cls, objectpath:str, **kwargs) -> str:
        options  = [cls.libpath, cls.pwd()]
        for option in options:
            path = option + '/' + objectpath.replace('.', '/') + '.py'
            if os.path.exists(path):
                return path
        raise ValueError(f'Path not found for objectpath {objectpath}')

        

    @classmethod
    def find_functions(cls, path = './', working=False):
        fns = []
        if os.path.isdir(path):
            path = os.path.abspath(path)
            for p in cls.glob(path+'/**/**.py', recursive=True):
                p_fns = cls.find_functions(p)
                file_object_path = cls.path2objectpath(p)
                p_fns = [file_object_path + '.' + f for f in p_fns]
                for fn in p_fns:
                    if working:
                        try:
                            cls.import_object(fn)
                        except Exception as e:
                            r = cls.detailed_error(e)
                            r['fn'] = fn
                            cls.print(r, color='red')
                            continue
                    fns += [fn]

        else:
            code = cls.get_text(path)
            for line in code.split('\n'):
                if line.startswith('def ') or line.startswith('async def '):
                    fn = line.split('def ')[-1].split('(')[0].strip()
                    fns += [fn]
        return fns
    

    @classmethod
    def find_async_functions(cls, path):
        if os.path.isdir(path):
            path2classes = {}
            for p in cls.glob(path+'/**/**.py', recursive=True):
                path2classes[p] = cls.find_functions(p)
            return path2classes
        code = cls.get_text(path)
        fns = []
        for line in code.split('\n'):
            if line.startswith('async def '):
                fn = line.split('def ')[-1].split('(')[0].strip()
                fns += [fn]
        return [c for c in fns]
    
    @classmethod
    def find_objects(cls, path:str = './', search=None, working=False, **kwargs):
        classes = cls.find_classes(path, working=working)
        functions = cls.find_functions(path, working=working)

        if search != None:
            classes = [c for c in classes if search in c]
            functions = [f for f in functions if search in f]
        object_paths = functions + classes
        return object_paths
    objs = find_objects

    

    def find_working_objects(self, path:str = './', **kwargs):
        objects = self.find_objects(path, **kwargs)
        working_objects = []
        progress = self.tqdm(objects, desc='Progress')
        error_progress = self.tqdm(objects, desc='Errors')

        for obj in objects:

            try:
                self.import_object(obj)
                working_objects += [obj]
                progress.update(1)
            except:
                error_progress.update(1)
                pass
        return working_objects

    search = find_objects

    @classmethod
    def simple2objectpath(cls, 
                          simple_path:str,
                           cactch_exception = False, 
                           **kwargs) -> str:

        object_path = cls.simple2path(simple_path, **kwargs)
        classes =  cls.find_classes(object_path)
        return classes[-1]

    @classmethod
    def simple2object(cls, path:str, **kwargs) -> str:
        path =  cls.simple2objectpath(path, **kwargs)
        try:
            return cls.import_object(path)
        except:
            path = cls.tree().get(path)
            return cls.import_object(path)
            
    included_pwd_in_path = False
    @classmethod
    def import_module(cls, 
                      import_path:str, 
                      included_pwd_in_path=True, 
                      try_prefixes = ['commune','commune.modules', 'modules', 'commune.subspace', 'subspace']
                      ) -> 'Object':
        from importlib import import_module
        if included_pwd_in_path and not cls.included_pwd_in_path:
            import sys
            pwd = cls.pwd()
            sys.path.append(pwd)
            sys.path = list(set(sys.path))
            cls.included_pwd_in_path = True
        # if commune is in the path more than once, we want to remove the duplicates
        if cls.libname in import_path:
            import_path = cls.libname + import_path.split(cls.libname)[-1]
        pwd = cls.pwd()
        try:
            return import_module(import_path)
        except Exception as _e:
            for prefix in try_prefixes:
                try:
                    return import_module(f'{prefix}.{import_path}')
                except Exception as e:
                    pass
            raise _e
    
    @classmethod
    def can_import_module(cls, module:str) -> bool:
        '''
        Returns true if the module is valid
        '''
        try:
            cls.import_module(module)
            return True
        except:
            return False
        

        
    def get_module_objects(self, path:str, **kwargs):
        if self.can_import_module(path):
            return self.find_objects(path.replace('.', '/'), **kwargs)
        return self.find_objects(path, **kwargs)
    @classmethod
    def can_import_object(cls, module:str) -> bool:
        '''
        Returns true if the module is valid
        '''
        try:
            cls.import_object(module)
            return True
        except:
            return False

    @classmethod
    def import_object(cls, key:str, verbose: bool = 0, trials=3)-> Any:
        '''
        Import an object from a string with the format of {module_path}.{object}
        Examples: import_object("torch.nn"): imports nn from torch
        '''
        module = '.'.join(key.split('.')[:-1])
        object_name = key.split('.')[-1]
        if verbose:
            cls.print(f'Importing {object_name} from {module}')
        obj =  getattr(cls.import_module(module), object_name)
        return obj
    
    obj = get_obj = import_object


    @classmethod
    def object_exists(cls, path:str, verbose=False)-> Any:
        try:
            cls.import_object(path, verbose=verbose)
            return True
        except Exception as e:
            return False
    
    imp = get_object = importobj = import_object

    @classmethod
    def module_exists(cls, module:str, **kwargs) -> bool:
        '''
        Returns true if the module exists
        '''
        try:
            module_path = c.simple2path(module)
            print(module_path)
            module_exists = c.exists(module_path)
        except:
            module_exists = False
        # if not module_exists:
        #     module_exists = module in c.modules()
        return module_exists
    
    @classmethod
    def has_app(cls, module:str, **kwargs) -> bool:
        return cls.module_exists(module + '.app', **kwargs)
    
    @classmethod
    def simplify_paths(cls,  paths):
        paths = [cls.simplify_path(p) for p in paths]
        paths = [p for p in paths if p]
        return paths

    @classmethod
    def simplify_path(cls, p, avoid_terms=['modules', 'agents']):
        chunks = p.split('.')
        if len(chunks) < 2:
            return None
        file_name = chunks[-2]
        chunks = chunks[:-1]
        path = ''
        for chunk in chunks:
            if chunk in path:
                continue
            path += chunk + '.'
        if file_name.endswith('_module'):
            path = '.'.join(path.split('.')[:-1])
        
        if path.startswith(cls.libname + '.'):
            path = path[len(cls.libname)+1:]

        if path.endswith('.'):
            path = path[:-1]

        if '_' in file_name:
            file_chunks =  file_name.split('_')
            if all([c in path for c in file_chunks]):
                path = '.'.join(path.split('.')[:-1])
        for avoid in avoid_terms:
            avoid = f'{avoid}.' 
            if avoid in path:
                path = path.replace(avoid, '')
        return path

    @classmethod
    def local_modules(cls, search=None):
        object_paths = cls.find_classes(cls.pwd())
        object_paths = cls.simplify_paths(object_paths) 
        if search != None:
            object_paths = [p for p in object_paths if search in p]
        return sorted(list(set(object_paths)))
    @classmethod
    def lib_tree(cls, ):
        return cls.get_tree(cls.libpath)
    @classmethod
    def local_tree(cls ):
        return cls.get_tree(cls.pwd())
    
    @classmethod
    def get_tree(cls, path):
        class_paths = cls.find_classes(path)
        simple_paths = cls.simplify_paths(class_paths) 
        return dict(zip(simple_paths, class_paths))
    
    @classmethod
    def get_module(cls, 
                   path:str = 'module',  
                   cache=True,
                   verbose = False,
                   update_tree_if_fail = True,
                   init_kwargs = None,
                   catch_error = False,
                   ) -> str:
        import commune as c
        path = path or 'module'
        if catch_error:
            try:
                return cls.get_module(path=path, cache=cache, 
                                      verbose=verbose, 
                                      update_tree_if_fail=update_tree_if_fail,
                                       init_kwargs=init_kwargs, 
                                       catch_error=False)
            except Exception as e:
                return c.detailed_error(e)
        if path in ['module', 'c']:
            return c.Module
        # if the module is a valid import path 
        shortcuts = c.shortcuts()
        if path in shortcuts:
            path = shortcuts[path]
        module = None
        cache_key = path
        t0 = c.time()
        if cache and cache_key in c.module_cache:
            module = c.module_cache[cache_key]
            return module
        module = c.simple2object(path)
        # ensure module
        if verbose:
            c.print(f'Loaded {path} in {c.time() - t0} seconds', color='green')
        
        if init_kwargs != None:
            module = module(**init_kwargs)
        is_module = c.is_module(module)
        if not is_module:
            module = cls.obj2module(module)
        if cache:
            c.module_cache[cache_key] = module            
        return module
    
    
    _tree = None
    @classmethod
    def tree(cls, search=None, cache=True):
        if cls._tree != None and cache:
            return cls._tree
        local_tree = cls.local_tree()
        lib_tree = cls.lib_tree()
        tree = {**local_tree, **lib_tree}
        if cache:
            cls._tree = tree
        if search != None:
            tree = {k:v for k,v in tree.items() if search in k}
        return tree

        return tree
    

    def overlapping_modules(self, search:str=None, **kwargs):
        local_modules = self.local_modules(search=search)
        lib_modules = self.lib_modules(search=search)
        return [m for m in local_modules if m in lib_modules]
    

    @classmethod
    def lib_modules(cls, search=None):
        object_paths = cls.find_classes(cls.libpath )
        object_paths = cls.simplify_paths(object_paths) 
        if search != None:
            object_paths = [p for p in object_paths if search in p]
        return sorted(list(set(object_paths)))
    
    @classmethod
    def find_modules(cls, search=None, **kwargs):
        local_modules = cls.local_modules(search=search)
        lib_modules = cls.lib_modules(search=search)
        return sorted(list(set(local_modules + lib_modules)))

    _modules = None
    @classmethod
    def modules(cls, search=None, cache=True,   **kwargs)-> List[str]:
        modules = cls._modules
        if not cache or modules == None:
            modules =  cls.find_modules(search=None, **kwargs)
        if search != None:
            modules = [m for m in modules if search in m]            
        return modules
    get_modules = modules

    @classmethod
    def has_module(cls, module):
        return module in cls.modules()
    



    
    def new_modules(self, *modules, **kwargs):
        for module in modules:
            self.new_module(module=module, **kwargs)



    @classmethod
    def new_module( cls,
                   module : str ,
                   base_module : str = 'demo', 
                   folder_module : bool = False,
                   update=1
                   ):
        
        import commune as c
        base_module = c.module(base_module)
        module_class_name = ''.join([m[0].capitalize() + m[1:] for m in module.split('.')])
        base_module_class_name = base_module.class_name()
        base_module_code = base_module.code().replace(base_module_class_name, module_class_name)
        pwd = c.pwd()
        path = os.path.join(pwd, module.replace('.', '/'))
        if folder_module:
            dirpath = path
            filename = module.replace('.', '_')
            path = os.path.join(path, filename)
        
        path = path + '.py'
        dirpath = os.path.dirname(path)
        if os.path.exists(path) and not update:
            return {'success': True, 'msg': f'Module {module} already exists', 'path': path}
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        c.put_text(path, base_module_code)
        
        return {'success': True, 'msg': f'Created module {module}', 'path': path}
    
    add_module = new_module


    @classmethod
    def has_local_module(cls, path=None):
        import commune as c 
        path = '.' if path == None else path
        if os.path.exists(f'{path}/module.py'):
            text = c.get_text(f'{path}/module.py')
            if 'class ' in text:
                return True
        return False
    


    def path2functions(self, path=None):
        path = path or (self.root_path + '/utils')
        paths = self.ls(path)
        path2functions = {}
        print(paths)
        
        for p in paths:

            functions = []
            if os.path.isfile(p) == False:
                continue
            text = self.get_text(p)
            if len(text) == 0:
                continue
            
            for line in text.split('\n'):
                print(line)
                if 'def ' in line and '(' in line:
                    functions.append(line.split('def ')[1].split('(')[0])
            replative_path = p[len(path)+1:]
            path2functions[replative_path] = functions
        return path2functions

    @staticmethod
    def chunk(sequence:list = [0,2,3,4,5,6,6,7],
            chunk_size:int=4,
            num_chunks:int= None):
        assert chunk_size != None or num_chunks != None, 'must specify chunk_size or num_chunks'
        if chunk_size == None:
            chunk_size = len(sequence) / num_chunks
        if chunk_size > len(sequence):
            return [sequence]
        if num_chunks == None:
            num_chunks = int(len(sequence) / chunk_size)
        if num_chunks == 0:
            num_chunks = 1
        chunks = [[] for i in range(num_chunks)]
        for i, element in enumerate(sequence):
            idx = i % num_chunks
            chunks[idx].append(element)
        return chunks
    
    @classmethod
    def batch(cls, x: list, batch_size:int=8): 
        return cls.chunk(x, chunk_size=batch_size)

    def cancel(self, futures):
        for f in futures:
            f.cancel()
        return {'success': True, 'msg': 'cancelled futures'}
       
    
    @classmethod
    def cachefn(cls, func, max_age=60, update=False, cache=True, cache_folder='cachefn'):
        import functools
        path_name = cache_folder+'/'+func.__name__
        def wrapper(*args, **kwargs):
            fn_name = func.__name__
            cache_params = {'max_age': max_age, 'cache': cache}
            for k, v in cache_params.items():
                cache_params[k] = kwargs.pop(k, v)

            
            if not update:
                result = cls.get(fn_name, **cache_params)
                if result != None:
                    return result

            result = func(*args, **kwargs)
            
            if cache:
                cls.put(fn_name, result, cache=cache)
            return result
        return wrapper


    @staticmethod
    def round(x:Union[float, int], sig: int=6, small_value: float=1.0e-9):
        from commune.utils.math import round_sig
        return round_sig(x, sig=sig, small_value=small_value)
    
    @classmethod
    def round_decimals(cls, x:Union[float, int], decimals: int=6, small_value: float=1.0e-9):
       
        import math
        """
        Rounds x to the number of {sig} digits
        :param x:
        :param sig: signifant digit
        :param small_value: smallest possible value
        :return:
        """
        x = float(x)
        return round(x, decimals)
    
    


    @staticmethod
    def num_words( text):
        return len(text.split(' '))
    
    @classmethod
    def random_word(cls, *args, n=1, seperator='_', **kwargs):
        import commune as c
        random_words = cls.module('key').generate_mnemonic(*args, **kwargs).split(' ')[0]
        random_words = random_words.split(' ')[:n]
        if n == 1:
            return random_words[0]
        else:
            return seperator.join(random_words.split(' ')[:n])

    @classmethod
    def filter(cls, text_list: List[str], filter_text: str) -> List[str]:
        return [text for text in text_list if filter_text in text]



    @staticmethod
    def tqdm(*args, **kwargs):
        from tqdm import tqdm
        return tqdm(*args, **kwargs)

    progress = tqdm

    emojis = {
        'smile': '😊',
        'sad': '😞',
        'heart': '❤️',
        'star': '⭐',
        'fire': '🔥',
        'check': '✅',
        'cross': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'question': '❓',
        'exclamation': '❗',
        'plus': '➕',
        'minus': '➖',

    }


    @classmethod
    def emoji(cls, name:str):
        return cls.emojis.get(name, '❓')

    @staticmethod
    def tqdm(*args, **kwargs):
        from tqdm import tqdm
        return tqdm(*args, **kwargs)
    progress = tqdm


    
    
    @classmethod
    def jload(cls, json_string):
        import json
        return json.loads(json_string.replace("'", '"'))

    @classmethod
    def partial(cls, fn, *args, **kwargs):
        return partial(fn, *args, **kwargs)
        
        
    @classmethod
    def sizeof(cls, obj):
        import sys
        sizeof = 0
        if isinstance(obj, dict):
            for k,v in obj.items():
                sizeof +=  cls.sizeof(k) + cls.sizeof(v)
        elif isinstance(obj, list):
            for v in obj:
                sizeof += cls.sizeof(v)
        elif any([k.lower() in cls.type_str(obj).lower() for k in ['torch', 'Tensor'] ]):

            sizeof += cls.get_tensor_size(obj)
        else:
            sizeof += sys.getsizeof(obj)
                
        return sizeof
    

    @classmethod
    def put_torch(cls, path:str, data:Dict,  **kwargs):
        import torch
        path = cls.resolve_path(path=path, extension='pt')
        torch.save(data, path)
        return path
    
    def init_nn(self):
        import torch
        torch.nn.Module.__init__(self)

    
    @classmethod
    def check_word(cls, word:str)-> str:
        import commune as c
        files = c.glob('./')
        progress = c.tqdm(len(files))
        for f in files:
            try:
                text = c.get_text(f)
            except Exception as e:
                continue
            if word in text:
                return True
            progress.update(1)
        return False
    
    @classmethod
    def wordinfolder(cls, word:str, path:str='./')-> bool:
        import commune as c
        path = c.resolve_path(path)
        files = c.glob(path)
        progress = c.tqdm(len(files))
        for f in files:
            try:
                text = c.get_text(f)
            except Exception as e:
                continue
            if word in text:
                return True
            progress.update(1)
        return False


    def locals2hash(self, kwargs:dict = {'a': 1}, keys=['kwargs']) -> str:
        kwargs.pop('cls', None)
        kwargs.pop('self', None)
        return self.dict2hash(kwargs)

    @classmethod
    def dict2hash(cls, d:dict) -> str:
        for k in d.keys():
            assert cls.jsonable(d[k]), f'{k} is not jsonable'
        return cls.hash(d)
    
    @classmethod
    def dict_put(cls, *args, **kwargs):
        from commune.utils.dict import dict_put
        return dict_put(*args, **kwargs)
    
    @classmethod
    def dict_get(cls, *args, **kwargs):
        from commune.utils.dict import dict_get
        return dict_get(*args, **kwargs)
    

    @classmethod
    def is_address(cls, address:str) -> bool:
        if not isinstance(address, str):
            return False
        if '://' in address:
            return True
        conds = []
        conds.append(len(address.split('.')) >= 3)
        conds.append(isinstance(address, str))
        conds.append(':' in address)
        conds.append(cls.is_int(address.split(':')[-1]))
        return all(conds)
    

    @classmethod
    def new_event_loop(cls, nest_asyncio:bool = True) -> 'asyncio.AbstractEventLoop':
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if nest_asyncio:
            cls.nest_asyncio()
        
        return loop
  

    def set_event_loop(self, loop=None, new_loop:bool = False) -> 'asyncio.AbstractEventLoop':
        import asyncio
        try:
            if new_loop:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            else:
                loop = loop if loop else asyncio.get_event_loop()
        except RuntimeError as e:
            self.new_event_loop()
            
        self.loop = loop
        return self.loop

    @classmethod
    def get_event_loop(cls, nest_asyncio:bool = True) -> 'asyncio.AbstractEventLoop':
        try:
            loop = asyncio.get_event_loop()
        except Exception as e:
            loop = cls.new_event_loop(nest_asyncio=nest_asyncio)
        return loop



      
    @classmethod
    def merge(cls,  from_obj= None, 
                        to_obj = None,
                        include_hidden:bool=True, 
                        allow_conflicts:bool=True, 
                        verbose: bool = False):
        
        '''
        Merge the functions of a python object into the current object (a)
        '''
        from_obj = from_obj or cls
        to_obj = to_obj or cls
        
        for fn in dir(from_obj):
            if fn.startswith('_') and not include_hidden:
                continue
            if hasattr(to_obj, fn) and not allow_conflicts:
                continue
            if verbose:
                cls.print(f'Adding {fn}')
            setattr(to_obj, fn, getattr(from_obj, fn))
            
        return to_obj
   
        
    # JUPYTER NOTEBOOKS
    @classmethod
    def enable_jupyter(cls):
        cls.nest_asyncio()
    

    
    jupyter = enable_jupyter
    

    @classmethod
    def pip_list(cls, lib=None):
        pip_list =  cls.cmd(f'pip list', verbose=False, bash=True).split('\n')
        if lib != None:
            pip_list = [l for l in pip_list if l.startswith(lib)]
        return pip_list
    
    
    @classmethod
    def pip_libs(cls):
        return list(cls.lib2version().values())
    
    @classmethod
    def ensure_lib(cls, lib:str, verbose:bool=False):
        if  cls.pip_exists(lib):
            return {'lib':lib, 'version':cls.version(lib), 'status':'exists'}
        elif cls.pip_exists(lib) == False:
            cls.pip_install(lib, verbose=verbose)
        return {'lib':lib, 'version':cls.version(lib), 'status':'installed'}

    required_libs = []
    @classmethod
    def ensure_libs(cls, libs: List[str] = None, verbose:bool=False):
        if hasattr(cls, 'libs'):
            libs = cls.libs
        results = []
        for lib in libs:
            results.append(cls.ensure_lib(lib, verbose=verbose))
        return results
    
    @classmethod
    def install(cls, libs: List[str] = None, verbose:bool=False):
        return cls.ensure_libs(libs, verbose=verbose)
    
    @classmethod
    def ensure_env(cls):
        cls.ensure_libs(cls.libs)
    
    ensure_package = ensure_lib

    @classmethod
    def queue(cls, size:str=-1, *args,  mode='queue', **kwargs):
        if mode == 'queue':
            return cls.import_object('queue.Queue')(size, *args, **kwargs)
        elif mode in ['multiprocessing', 'mp', 'process']:
            return cls.module('process')(size, *args, **kwargs)
        elif mode == 'ray':
            return cls.import_object('ray.util.queue.Queue')(size, *args, **kwargs)
        elif mode == 'redis':
            return cls.import_object('redis.Queue')(size, *args, **kwargs)
        elif mode == 'rabbitmq':
            return cls.import_object('pika.Queue')(size, *args, **kwargs)
        else:
            raise NotImplementedError(f'mode {mode} not implemented')
    



    @staticmethod
    def is_class(module: Any) -> bool:
        return type(module).__name__ == 'type' 
    




    @classmethod
    def param_keys(cls, model:'nn.Module' = None)->List[str]:
        model = cls.resolve_model(model)
        return list(model.state_dict().keys())
    
    @classmethod
    def params_map(cls, model, fmt='b'):
        params_map = {}
        state_dict = cls.resolve_model(model).state_dict()
        for k,v in state_dict.items():
            params_map[k] = {'shape': list(v.shape) ,
                             'size': cls.get_tensor_size(v, fmt=fmt),
                             'dtype': str(v.dtype),
                             'requires_grad': v.requires_grad,
                             'device': v.device,
                             'numel': v.numel(),
                             
                             }
            
        return params_map
    


    @classmethod
    def get_shortcut(cls, shortcut:str) -> dict:
        return cls.shortcuts().get(shortcut)
 
    @classmethod
    def rm_shortcut(cls, shortcut) -> str:
        shortcuts = cls.shortcuts()
        if shortcut in shortcuts:
            cls.shortcuts.pop(shortcut)
            cls.put_json('shortcuts', cls.shortcuts)
        return shortcut
    


    @classmethod
    def repo_url(cls, *args, **kwargs):
        return cls.module('git').repo_url(*args, **kwargs)    
    




    @classmethod
    def compose(cls, *args, **kwargs):
        return cls.module('docker').compose(*args, **kwargs)


    @classmethod
    def ps(cls, *args, **kwargs):
        return cls.get_module('docker').ps(*args, **kwargs)
 
    @classmethod
    def has_gpus(cls): 
        return bool(len(cls.gpus())>0)


    @classmethod
    def split_gather(cls,jobs:list, n=3,  **kwargs)-> list:
        if len(jobs) < n:
            return cls.gather(jobs, **kwargs)
        gather_jobs = [asyncio.gather(*job_chunk) for job_chunk in cls.chunk(jobs, num_chunks=n)]
        gather_results = cls.gather(gather_jobs, **kwargs)
        results = []
        for gather_result in gather_results:
            results += gather_result
        return results
    
    @classmethod
    def addresses(cls, *args, **kwargs) -> List[str]:
        return list(cls.namespace(*args,**kwargs).values())

    @classmethod
    def address_exists(cls, address:str) -> List[str]:
        addresses = cls.addresses()
        return address in addresses
    

        
    @classmethod
    def task(cls, fn, timeout=1, mode='asyncio'):
        
        if mode == 'asyncio':
            assert callable(fn)
            future = asyncio.wait_for(fn, timeout=timeout)
            return future
        else:
            raise NotImplemented
        
    
    @classmethod
    def shuffle(cls, x:list)->list:
        if len(x) == 0:
            return x
        random.shuffle(x)
        return x
    

    @staticmethod
    def retry(fn, trials:int = 3, verbose:bool = True):
        # if fn is a self method, then it will be a bound method, and we need to get the function
        if hasattr(fn, '__self__'):
            fn = fn.__func__
        def wrapper(*args, **kwargs):
            for i in range(trials):
                try:
                    cls.print(fn)
                    return fn(*args, **kwargs)
                except Exception as e:
                    if verbose:
                        cls.print(cls.detailed_error(e), color='red')
                        cls.print(f'Retrying {fn.__name__} {i+1}/{trials}', color='red')

        return wrapper
    

    @staticmethod
    def reverse_map(x:dict)->dict:
        '''
        reverse a dictionary
        '''
        return {v:k for k,v in x.items()}

    @classmethod
    def df(cls, x, **kwargs):
        return cls.import_object('pandas.DataFrame')(x, **kwargs)

    @classmethod
    def torch(cls):
        return cls.import_module('torch')

    @classmethod
    def tensor(cls, *args, **kwargs):
        return cls.import_object('torch.tensor')(*args, **kwargs)


    @staticmethod
    def random_int(start_value=100, end_value=None):
        if end_value == None: 
            end_value = start_value
            start_value, end_value = 0 , start_value
        
        assert start_value != None, 'start_value must be provided'
        assert end_value != None, 'end_value must be provided'
        return random.randint(start_value, end_value)
    


    def mean(self, x:list=[0,1,2,3,4,5,6,7,8,9,10]):
        if not isinstance(x, list):
            x = list(x)
        return sum(x) / len(x)
    
    def median(self, x:list=[0,1,2,3,4,5,6,7,8,9,10]):
        if not isinstance(x, list):
            x = list(x)
        x = sorted(x)
        n = len(x)
        if n % 2 == 0:
            return (x[n//2] + x[n//2 - 1]) / 2
        else:
            return x[n//2]
    
    @classmethod
    def stdev(cls, x:list= [0,1,2,3,4,5,6,7,8,9,10], p=2):
        if not isinstance(x, list):
            x = list(x)
        mean = cls.mean(x)
        return (sum([(i - mean)**p for i in x]) / len(x))**(1/p)
    std = stdev

    @classmethod
    def set_env(cls, key:str, value:str)-> None:
        '''
        Pay attention to this function. It sets the environment variable
        '''
        os.environ[key] = value
        return value 

    
    @classmethod
    def pwd(cls):
        pwd = os.getenv('PWD', cls.libpath) # the current wor king directory from the process starts 
        return pwd
    
    @classmethod
    def choice(cls, options:Union[list, dict])->list:
        options = deepcopy(options) # copy to avoid changing the original
        if len(options) == 0:
            return None
        if isinstance(options, dict):
            options = list(options.values())
        assert isinstance(options, list),'options must be a list'
        return random.choice(options)

    @classmethod
    def sample(cls, options:list, n=2):
        if isinstance(options, int):
            options = list(range(options))
        options = cls.shuffle(options)
        return options[:n]
        
    @classmethod
    def chown(cls, path:str = None, sudo:bool =True):
        path = cls.resolve_path(path)
        user = cls.env('USER')
        cmd = f'chown -R {user}:{user} {path}'
        cls.cmd(cmd , sudo=sudo, verbose=True)
        return {'success':True, 'message':f'chown cache {path}'}

    @classmethod
    def chown_cache(cls, sudo:bool = True):
        return cls.chown(cls.cache_path, sudo=sudo)
        
    @classmethod
    def colors(cls):
        return ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white']
    colours = colors
    @classmethod
    def random_color(cls):
        return random.choice(cls.colors())
    randcolor = randcolour = colour = color = random_colour = random_color


    def get_util(self, util:str):
        return self.get_module(util)

    @classmethod
    def random_float(cls, min=0, max=1):
        return random.uniform(min, max)

    @classmethod
    def random_ratio_selection(cls, x:list, ratio:float = 0.5)->list:
        if type(x) in [float, int]:
            x = list(range(int(x)))
        assert len(x)>0
        if ratio == 1:
            return x
        assert ratio > 0 and ratio <= 1
        random.shuffle(x)
        k = max(int(len(x) * ratio),1)
        return x[:k]


    def link_cmd(cls, old, new):
        
        link_cmd = cls.get('link_cmd', {})
        assert isinstance(old, str), old
        assert isinstance(new, str), new
        link_cmd[new] = old 
        
        cls.put('link_cmd', link_cmd)


    
              
    @classmethod
    def resolve_memory(cls, memory: Union[str, int, float]) -> str:
                    
        scale_map = {
            'kb': 1e3,
            'mb': 1e6,
            'gb': 1e9,
            'b': 1,
        }
        if isinstance(memory, str):
            scale_found = False
            for scale_key, scale_value in scale_map.items():
                
                
                if isinstance(memory, str) and memory.lower().endswith(scale_key):
                    memory = int(int(memory[:-len(scale_key)].strip())*scale_value)
                    
    
                if type(memory) in [float, int]:
                    scale_found = True
                    break
                    
        assert type(memory) in [float, int], f'memory must be a float or int, got {type(memory)}'
        return memory
            

    
    @classmethod
    def filter(cls, text_list: List[str], filter_text: str) -> List[str]:
        return [text for text in text_list if filter_text in text]


    @classmethod
    def is_success(cls, x):
        # assume that if the result is a dictionary, and it has an error key, then it is an error
        if isinstance(x, dict):
            if 'error' in x:
                return False
            if 'success' in x and x['success'] == False:
                return False
            
        return True
    
    @classmethod
    def is_error(cls, x:Any):
        """
        The function checks if the result is an error
        The error is a dictionary with an error key set to True
        """
        if isinstance(x, dict):
            if 'error' in x and x['error'] == True:
                return True
            if 'success' in x and x['success'] == False:
                return True
        return False
    
    @classmethod
    def is_int(cls, value) -> bool:
        o = False
        try :
            int(value)
            if '.' not in str(value):
                o =  True
        except:
            pass
        return o
    
        
    @classmethod
    def is_float(cls, value) -> bool:
        o =  False
        try :
            float(value)
            if '.' in str(value):
                o = True
        except:
            pass

        return o 



    @classmethod
    def timer(cls, *args, **kwargs):
        from commune.utils.time import Timer
        return Timer(*args, **kwargs)
    
    @classmethod
    def timeit(cls, fn, *args, include_result=False, **kwargs):

        t = cls.time()
        if isinstance(fn, str):
            fn = cls.get_fn(fn)
        result = fn(*args, **kwargs)
        response = {
            'latency': cls.time() - t,
            'fn': fn.__name__,
            
        }
        if include_result:
            print(response)
            return result
        return response

    @staticmethod
    def remotewrap(fn, remote_key:str = 'remote'):
        '''
        calls your function if you wrap it as such

        @c.remotewrap
        def fn():
            pass
            
        # deploy it as a remote function
        fn(remote=True)
        '''
    
        def remotewrap(self, *args, **kwargs):
            remote = kwargs.pop(remote_key, False)
            if remote:
                return self.remote_fn(module=self, fn=fn.__name__, args=args, kwargs=kwargs)
            else:
                return fn(self, *args, **kwargs)
        
        return remotewrap
    

    @staticmethod
    def is_mnemonic(s: str) -> bool:
        import re
        # Match 12 or 24 words separated by spaces
        return bool(re.match(r'^(\w+ ){11}\w+$', s)) or bool(re.match(r'^(\w+ ){23}\w+$', s))

    @staticmethod   
    def is_private_key(s: str) -> bool:
        import re
        # Match a 64-character hexadecimal string
        pattern = r'^[0-9a-fA-F]{64}$'
        return bool(re.match(pattern, s))


    
    @staticmethod
    def address2ip(address:str) -> str:
        return str('.'.join(address.split(':')[:-1]))

    @staticmethod
    def as_completed( futures, timeout=10, **kwargs):
        return concurrent.futures.as_completed(futures, timeout=timeout, **kwargs)


    @classmethod
    def dict2munch(cls, x:dict, recursive:bool=True)-> 'Munch':
        from munch import Munch
        '''
        Turn dictionary into Munch
        '''
        if isinstance(x, dict):
            for k,v in x.items():
                if isinstance(v, dict) and recursive:
                    x[k] = cls.dict2munch(v)
            x = Munch(x)
        return x 

    @classmethod
    def munch2dict(cls, x:'Munch', recursive:bool=True)-> dict:
        from munch import Munch
        '''
        Turn munch object  into dictionary
        '''
        if isinstance(x, Munch):
            x = dict(x)
            for k,v in x.items():
                if isinstance(v, Munch) and recursive:
                    x[k] = cls.munch2dict(v)

        return x 

    
    @classmethod
    def munch(cls, x:Dict) -> 'Munch':
        '''
        Converts a dict to a munch
        '''
        return cls.dict2munch(x)
    

    @classmethod  
    def time( cls, t=None) -> float:
        import time
        if t is not None:
            return time.time() - t
        else:
            return time.time()

    @classmethod
    def datetime(cls):
        import datetime
        # UTC 
        return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")

    @classmethod
    def time2datetime(cls, t:float):
        import datetime
        return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d_%H:%M:%S")
    
    time2date = time2datetime

    @classmethod
    def datetime2time(cls, x:str):
        import datetime
        return datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timestamp()
    
    date2time =  datetime2time

    @classmethod
    def delta_t(cls, t):
        return t - cls.time()
    @classmethod
    def timestamp(cls) -> float:
        return int(cls.time())
    @classmethod
    def sleep(cls, seconds:float) -> None:
        import time
        time.sleep(seconds)
        return None
    

    def search_dict(self, d:dict = 'k,d', search:str = {'k.d': 1}) -> dict:
        search = search.split(',')
        new_d = {}

        for k,v in d.items():
            if search in k.lower():
                new_d[k] = v
        
        return new_d

    @classmethod
    def path2text(cls, path:str, relative=False):

        path = cls.resolve_path(path)
        assert os.path.exists(path), f'path {path} does not exist'
        if os.path.isdir(path):
            filepath_list = cls.glob(path + '/**')
        else:
            assert os.path.exists(path), f'path {path} does not exist'
            filepath_list = [path] 
        path2text = {}
        for filepath in filepath_list:
            try:
                path2text[filepath] = cls.get_text(filepath)
            except Exception as e:
                pass
        if relative:
            pwd = cls.pwd()
            path2text = {os.path.relpath(k, pwd):v for k,v in path2text.items()}
        return path2text

    @classmethod
    def root_key(cls):
        return cls.get_key()

    @classmethod
    def root_key_address(cls) -> str:
        return cls.root_key().ss58_address


    @classmethod
    def is_root_key(cls, address:str)-> str:
        return address == cls.root_key().ss58_address

    # time within the context
    @classmethod
    def context_timer(cls, *args, **kwargs):
        return cls.timer(*args, **kwargs)
    

    @classmethod
    def folder_structure(cls, path:str='./', search='py', max_depth:int=5, depth:int=0)-> dict:
        import glob
        files = cls.glob(path + '/**')
        results = []
        for file in files:
            if os.path.isdir(file):
                cls.folder_structure(file, search=search, max_depth=max_depth, depth=depth+1)
            else:
                if search in file:
                    results.append(file)

        return results


    @classmethod
    def copy(cls, data: Any) -> Any:
        import copy
        return copy.deepcopy(data)
    

    @classmethod
    def find_word(cls, word:str, path='./')-> str:
        import commune as c
        path = c.resolve_path(path)
        files = c.glob(path)
        progress = c.tqdm(len(files))
        found_files = {}
        for f in files:
            try:
                text = c.get_text(f)
                if word not in text:
                    continue
                lines = text.split('\n')
            except Exception as e:
                continue
            
            line2text = {i:line for i, line in enumerate(lines) if word in line}
            found_files[f[len(path)+1:]]  = line2text
            progress.update(1)
        return found_files
    

        
    @classmethod
    def pip_install(cls, 
                    lib:str= None,
                    upgrade:bool=True ,
                    verbose:str=True,
                    ):
        import commune as c

        if lib in c.modules():
            c.print(f'Installing {lib} Module from local directory')
            lib = c.resolve_object(lib).dirpath()
        if lib == None:
            lib = c.libpath

        if c.exists(lib):
            cmd = f'pip install -e'
        else:
            cmd = f'pip install'
            if upgrade:
                cmd += ' --upgrade'
        return cls.cmd(cmd, verbose=verbose)


    @classmethod
    def pip_exists(cls, lib:str, verbose:str=True):
        return bool(lib in cls.pip_libs())
    

    @classmethod
    def hash(cls, x, mode: str='sha256',*args,**kwargs) -> str:
        import hashlib
        x = cls.python2str(x)
        if mode == 'keccak':
            return cls.import_object('web3.main.Web3').keccak(text=x, *args, **kwargs).hex()
        elif mode == 'ss58':
            return cls.import_object('scalecodec.utils.ss58.ss58_encode')(x, *args,**kwargs) 
        elif mode == 'python':
            return hash(x)
        elif mode == 'md5':
            return hashlib.md5(x.encode()).hexdigest()
        elif mode == 'sha256':
            return hashlib.sha256(x.encode()).hexdigest()
        elif mode == 'sha512':
            return hashlib.sha512(x.encode()).hexdigest()
        elif mode =='sha3_512':
            return hashlib.sha3_512(x.encode()).hexdigest()
        else:
            raise ValueError(f'unknown mode {mode}')
    
    @classmethod
    def hash_modes(cls):
        return ['keccak', 'ss58', 'python', 'md5', 'sha256', 'sha512', 'sha3_512']
    
    str2hash = hash
   

    def set_api_key(self, api_key:str, cache:bool = True):
        api_key = os.getenv(str(api_key), None)
        if api_key == None:
            api_key = self.get_api_key()
        self.api_key = api_key
        if cache:
            self.add_api_key(api_key)
        assert isinstance(api_key, str)

    
    def add_api_key(self, api_key:str, path=None):
        assert isinstance(api_key, str)
        path = self.resolve_path(path or 'api_keys')
        api_keys = self.get(path, [])
        api_keys.append(api_key)
        api_keys = list(set(api_keys))
        self.put(path, api_keys)
        return {'api_keys': api_keys}
    
    def set_api_keys(self, api_keys:str):
        api_keys = list(set(api_keys))
        self.put('api_keys', api_keys)
        return {'api_keys': api_keys}
    
    def rm_api_key(self, api_key:str):
        assert isinstance(api_key, str)
        api_keys = self.get(self.resolve_path('api_keys'), [])
        for i in range(len(api_keys)):
            if api_key == api_keys[i]:
                api_keys.pop(i)
                break   
        path = self.resolve_path('api_keys')
        self.put(path, api_keys)
        return {'api_keys': api_keys}

    def get_api_key(self, module=None):
        if module != None:
            self = self.module(module)
        api_keys = self.api_keys()
        if len(api_keys) == 0:
            raise 
        else:
            return self.choice(api_keys)

    def api_keys(self):
        return self.get(self.resolve_path('api_keys'), [])
    

    def rm_api_keys(self):
        self.put(self.resolve_path('api_keys'), [])
        return {'api_keys': []}




    thread_map = {}

    @classmethod
    def wait(cls, futures:list, timeout:int = None, generator:bool=False, return_dict:bool = True) -> list:
        is_singleton = bool(not isinstance(futures, list))

        futures = [futures] if is_singleton else futures
        # if type(futures[0]) in [asyncio.Task, asyncio.Future]:
        #     return cls.gather(futures, timeout=timeout)
            
        if len(futures) == 0:
            return []
        if cls.is_coroutine(futures[0]):
            return cls.gather(futures, timeout=timeout)
        
        future2idx = {future:i for i,future in enumerate(futures)}

        if timeout == None:
            if hasattr(futures[0], 'timeout'):
                timeout = futures[0].timeout
            else:
                timeout = 30
    
        if generator:
            def get_results(futures):
                try: 
                    for future in concurrent.futures.as_completed(futures, timeout=timeout):
                        if return_dict:
                            idx = future2idx[future]
                            yield {'idx': idx, 'result': future.result()}
                        else:
                            yield future.result()
                except Exception as e:
                    yield None
                
        else:
            def get_results(futures):
                results = [None]*len(futures)
                try:
                    for future in concurrent.futures.as_completed(futures, timeout=timeout):
                        idx = future2idx[future]
                        results[idx] = future.result()
                        del future2idx[future]
                    if is_singleton: 
                        results = results[0]
                except Exception as e:
                    unfinished_futures = [future for future in futures if future in future2idx]
                    cls.print(f'Error: {e}, {len(unfinished_futures)} unfinished futures with timeout {timeout} seconds')
                return results

        return get_results(futures)



    @classmethod
    def gather(cls,jobs:list, timeout:int = 20, loop=None)-> list:

        if loop == None:
            loop = cls.get_event_loop()

        if not isinstance(jobs, list):
            singleton = True
            jobs = [jobs]
        else:
            singleton = False

        assert isinstance(jobs, list) and len(jobs) > 0, f'Invalid jobs: {jobs}'
        # determine if we are using asyncio or multiprocessing

        # wait until they finish, and if they dont, give them none

        # return the futures that done timeout or not
        async def wait_for(future, timeout):
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                result = {'error': f'TimeoutError: {timeout} seconds'}

            return result
        
        jobs = [wait_for(job, timeout=timeout) for job in jobs]
        future = asyncio.gather(*jobs)
        results = loop.run_until_complete(future)

        if singleton:
            return results[0]
        return results
    



    @classmethod
    def submit(cls, 
                fn, 
                params = None,
                kwargs: dict = None, 
                args:list = None, 
                timeout:int = 40, 
                return_future:bool=True,
                init_args : list = [],
                init_kwargs:dict= {},
                executor = None,
                module: str = None,
                mode:str='thread',
                max_workers : int = 100,
                ):
        kwargs = {} if kwargs == None else kwargs
        args = [] if args == None else args
        if params != None:
            if isinstance(params, dict):
                kwargs = {**kwargs, **params}
            elif isinstance(params, list):
                args = [*args, *params]
            else:
                raise ValueError('params must be a list or a dictionary')
        
        fn = cls.get_fn(fn)
        executor = cls.executor(max_workers=max_workers, mode=mode) if executor == None else executor
        args = cls.copy(args)
        kwargs = cls.copy(kwargs)
        init_kwargs = cls.copy(init_kwargs)
        init_args = cls.copy(init_args)
        if module == None:
            module = cls
        else:
            module = cls.module(module)
        if isinstance(fn, str):
            method_type = cls.classify_fn(getattr(module, fn))
        elif callable(fn):
            method_type = cls.classify_fn(fn)
        else:
            raise ValueError('fn must be a string or a callable')
        
        if method_type == 'self':
            module = module(*init_args, **init_kwargs)

        future = executor.submit(fn=fn, args=args, kwargs=kwargs, timeout=timeout)

        if not hasattr(cls, 'futures'):
            cls.futures = []
        
        cls.futures.append(future)
            
        
        if return_future:
            return future
        else:
            return cls.wait(future, timeout=timeout)

    @classmethod
    def submit_batch(cls,  fn:str, batch_kwargs: List[Dict[str, Any]], return_future:bool=False, timeout:int=10, module = None,  *args, **kwargs):
        n = len(batch_kwargs)
        module = cls if module == None else module
        executor = cls.executor(max_workers=n)
        futures = [ executor.submit(fn=getattr(module, fn), kwargs=batch_kwargs[i], timeout=timeout) for i in range(n)]
        if return_future:
            return futures
        return cls.wait(futures)

   
    executor_cache = {}
    @classmethod
    def executor(cls, max_workers:int=None, mode:str="thread", maxsize=200, **kwargs):
        return c.module(f'executor')(max_workers=max_workers, maxsize=maxsize ,mode=mode, **kwargs)
    
    @staticmethod
    def detailed_error(e) -> dict:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        file_name = tb[-1].filename
        line_no = tb[-1].lineno
        line_text = tb[-1].line
        response = {
            'success': False,
            'error': str(e),
            'file_name': file_name,
            'line_no': line_no,
            'line_text': line_text
        }   
        return response
    

    @classmethod
    def as_completed(cls , futures:list, timeout:int=10, **kwargs):
        return concurrent.futures.as_completed(futures, timeout=timeout)
    
    @classmethod
    def is_coroutine(cls, future):
        """
        returns True if future is a coroutine
        """
        return cls.obj2typestr(future) == 'coroutine'


    @classmethod
    def obj2typestr(cls, obj):
        return str(type(obj)).split("'")[1]

    @classmethod
    def tasks(cls, task = None, mode='pm2',**kwargs) -> List[str]:
        kwargs['network'] = 'local'
        kwargs['update'] = False
        modules = cls.servers( **kwargs)
        tasks = getattr(cls, f'{mode}_list')(task)
        tasks = list(filter(lambda x: x not in modules, tasks))
        return tasks


    @classmethod
    def asubmit(cls, fn:str, *args, **kwargs):
        
        async def _asubmit():
            kwargs.update(kwargs.pop('kwargs',{}))
            return fn(*args, **kwargs)
        return _asubmit()



    thread_map = {}
    
    @classmethod
    def thread(cls,fn: Union['callable', str],  
                    args:list = None, 
                    kwargs:dict = None, 
                    daemon:bool = True, 
                    name = None,
                    tag = None,
                    start:bool = True,
                    tag_seperator:str='::', 
                    **extra_kwargs):
        
        if isinstance(fn, str):
            fn = cls.get_fn(fn)
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}

        assert callable(fn), f'target must be callable, got {fn}'
        assert  isinstance(args, list), f'args must be a list, got {args}'
        assert  isinstance(kwargs, dict), f'kwargs must be a dict, got {kwargs}'
        
        # unique thread name
        if name == None:
            name = fn.__name__
            cnt = 0
            while name in cls.thread_map:
                cnt += 1
                if tag == None:
                    tag = ''
                name = name + tag_seperator + tag + str(cnt)
        
        if name in cls.thread_map:
            cls.thread_map[name].join()

        t = threading.Thread(target=fn, args=args, kwargs=kwargs, **extra_kwargs)
        # set the time it starts
        setattr(t, 'start_time', cls.time())
        t.daemon = daemon
        if start:
            t.start()
        cls.thread_map[name] = t
        return t
    
    @classmethod
    def threads(cls, search:str = None):
        threads =  list(cls.thread_map.keys())
        if search != None:
            threads = [t for t in threads if search in t]
        return threads





c.enable_routes()
# c.add_utils()

Module = c # Module is alias of c
Module.run(__name__)


