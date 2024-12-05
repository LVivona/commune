import os
import inspect
import json
import shutil
import time
import sys
import argparse
from functools import partial
import os
from copy import deepcopy
from typing import *
import nest_asyncio
nest_asyncio.apply()

class c:
    libname  = lib = __file__.split('/')[-2]# the name of the library
    endpoints = ['ask', 'generate', 'forward']
    core_features = ['module_name', 'module_class',  'filepath', 'dirpath', 'tree']
    organization = org = orgname = 'commune-ai' # the organization
    cost = 1
    description = """This is a module"""
    base_module = 'module' # the base module
    git_host  = 'https://github.com'
    giturl = f'{git_host}/{org}/{libname}.git' # tge gutg
    default_port_range = [50050, 50150] # the port range between 50050 and 50150
    default_ip = local_ip = loopback = '0.0.0.0'   
    rootpath = root_path  = root  = '/'.join(__file__.split('/')[:-1]) 
    homepath = home_path  = os.path.expanduser('~') # the home path
    libpath = lib_path  = os.path.dirname(root_path) # the path to the library
    repopath = repo_path  = os.path.dirname(root_path) # the path to the repo
    modulespath = modules_path = os.path.dirname(__file__) + '/modules'
    docspath = docs_path = libname + '/docs'
    storagepath = storage_path = os.path.expanduser(f'~/.{libname}')
    cache = {} # cache for module objects
    shortcuts =  {
        'openai' : 'model.openai',
        'openrouter':  'model.openrouter',
        'or' : ' model.openrouter',
        'r' :  'remote',
        's' :  'network.subspace',
        'subspace': 'network.subspace', 
        'namespace': 'network', 
        'local': 'network',
        'network.local': 'network',
        }
    splitters = [':', '/', '.']

    @classmethod
    def module(cls, 
               path:str = 'module', 
               shortcuts : dict = None,
               cache=True, 
               trials=1, 
               tree:dict=None, 
               **extra_kwargs ) -> str:
        path = path or 'module'
        if path.endswith('.py'):
            path = c.path2name(path)
        else:
            path = path.replace('/','.')
            
        og_path = path

        if path in c.module_cache and cache:
            return c.module_cache[path]
        if path in ['module', c.libname[0]]:
            return c
        tree = tree or c.tree()
        path = tree.get(path, path)
        shortcuts = shortcuts or c.shortcuts
        path = shortcuts.get(path, path)
        try:
            module = c.import_object(path)
        except Exception as e:
            if trials == 0:
                raise ValueError(f'Error in module {og_path} {e}')
            return c.module(path,cache=cache, tree=c.tree(max_age=10), trials=trials-1)
        if not hasattr(module, 'module_name'):
            module.module_class = lambda *args, **kwargs : c.module_class(module)
            module.module_name = module.name = lambda *args, **kwargs : c.module_name(module)
            module.key = c.get_key(module.module_name(), create_if_not_exists=True)
            module.resolve_object = lambda *args, **kwargs : c.resolve_object(module)
            module.filepath = lambda *args, **kwargs : c.filepath(module)
            module.dirpath = lambda *args, **kwargs : c.dirpath(module)
            module.code = lambda *args, **kwargs : c.code(module)
            module.schema = lambda *args, **kwargs : c.schema(module)
            module.fns = module.functions = lambda *args, **kwargs : c.get_functions(module)
            module.fn2code = lambda *args, **kwargs : c.fn2code(module)
            module.ask = lambda *args, **kwargs : c.ask(*args, module=module, **kwargs)
            module.config = lambda *args, **kwargs : c.config(module=module, **kwargs)
        if cache:
            c.module_cache[path] = module      
        return module
    block =  get_block = get_module =   module
    
    @classmethod
    def filepath(cls, obj=None) -> str:
        obj = cls.resolve_object(obj)
        try:
            module_path =  inspect.getfile(obj)
        except Exception as e:
            c.print(f'Error: {e} {cls}', color='red')
            module_path =  inspect.getfile(cls)
        return module_path
    
    @classmethod
    def dirpath(cls, obj=None) -> str:
        return os.path.dirname(cls.filepath(obj))
    
    dir_path =  dirpath
    @classmethod
    def module_name(cls, obj=None):
        obj = obj or cls
        module_file =  inspect.getfile(obj)
        return c.path2name(module_file)
    path  = name = module_name 

    def vs(self, path = None):
        path = path or c.libpath
        path = c.abspath(path)
        return c.cmd(f'code {path}')
    
    @classmethod
    def module_class(cls, obj=None) -> str:
        return (obj or cls).__name__

    @classmethod
    def class_name(cls, obj= None) -> str:
        obj = obj if obj != None else cls
        return obj.__name__

    @classmethod
    def config_path(cls, obj = None) -> str:
        obj = obj or cls
        return obj.filepath()[:-3] + '.yaml'

    @classmethod
    def sandbox(cls, path='./', filename='sandbox.py'):
        for file in  c.files(path):
            if file.endswith(filename):
                return c.cmd(f'python {file}', verbose=True)
        return {'success': False, 'message': 'sandbox not found'}
    
    sand = sandbox

    module_cache = {}
    _obj = None

    def sync(self):
        return {'tree': c.tree(update=1), 'namespace':c.namespace(update=1), 'ip': c.ip()}
    
    def syspath(self):
        return sys.path
    
    @classmethod
    def storage_dir(cls):
        return f'{c.storage_path}/{cls.module_name()}'

    @classmethod
    def __str__(cls):
        return cls.__name__
    @classmethod
    def is_module(cls, obj=None) -> bool:
        
        if obj is None:
            obj = cls
        if all([hasattr(obj, k) for k in c.core_features]):
            return True
        return False
    
    @classmethod
    def is_root(cls, obj=None) -> bool:
        obj = obj or cls
        return bool(c.is_module(obj) and obj.module_class() == c.module_class())

    def print( *text:str,  **kwargs):
        if len(text) == 0:
            return
        if c.is_generator(text[0]):
            for t in text[0]:
                c.print(t, end='')
        else:
            return c.obj('commune.utils.misc.print')(*text, **kwargs)

    def is_error( *text:str,  **kwargs):
        return c.obj('commune.utils.misc.is_error')(*text, **kwargs)

    
    is_module_root = is_root_module = is_root

    @classmethod
    def resolve_object(cls, obj:str = None, **kwargs):
        if obj == None:
            obj = cls._obj if cls._obj else cls
        elif isinstance(obj, str):
            if c.object_exists(obj):
                obj =  c.obj(obj)
            elif c.module_exists(obj):
                obj =  c.module(obj)
            elif c.is_fn(obj):
                obj =  c.get_fn(obj)

        assert obj != None, f'Object {obj} does not exist'

        return obj
    
    @classmethod
    def pwd(cls):
        pwd = os.getcwd() # the current wor king directory from the process starts 
        return pwd
                            
    @classmethod
    def argparse(cls):
        parser = argparse.ArgumentParser(description='Argparse for the module')
        parser.add_argument('-m', '--m', '--module', '-module', dest='module', help='The function', type=str, default=cls.module_name())
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
    
    # UNDER CONSTRUCTION (USE WITH CAUTION)
    
    def setattr(self, k, v):
        setattr(self, k, v)

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
        assert c.jsonable(state_dict), 'State dict must be jsonable'
        return json.dumps(state_dict)
    
    @classmethod
    def from_json(cls, json_str:str) -> 'Module':
        import json
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def test_fns(cls, *args, **kwargs):
        return [f for f in cls.functions(*args, **kwargs) if f.startswith('test_')]
    tests_path = f'{libpath}/tests'
    @classmethod
    def pytest(cls, *args, **kwargs):
    
        return c.cmd(f'pytest {c.tests_path}',  stream=1, *args, **kwargs)
    
    @classmethod
    def argv(cls, include_script:bool = False):
        import sys
        args = sys.argv
        if include_script:
            return args
        else:
            return args[1:]

    @classmethod
    def is_module_file(cls, module = None) -> bool:
        if module != None:
            cls = c.module(module)
        dirpath = cls.dirpath()
        filepath = cls.filepath()
        return bool(dirpath.split('/')[-1] != filepath.split('/')[-1].split('.')[0])


    is_file_module = is_module_file

    @classmethod
    def is_module_folder(cls,  module = None) -> bool:
        if module != None:
            cls = c.module(module)
        return not cls.is_file_module()
    
    is_folder_module = is_module_folder 

    @classmethod
    def get_key(cls,key:str = None , **kwargs) -> None:
        from commune.key import Key
        return Key.get_key(key, **kwargs)
    key = get_key

    @classmethod
    def files(cls, 
              path='./', 
              search:str = None, 
              avoid_terms = ['__pycache__', '.git', '.ipynb_checkpoints', 'node_modules', 'artifacts', 'egg-info'], 
              **kwargs) -> List[str]:
        files =c.glob(path, **kwargs)
        files = [f for f in files if not any([at in f for at in avoid_terms])]
        if search != None:
            files = [f for f in files if search in files]
        return files

    @classmethod
    def num_files(cls, path='./',  **kwargs) -> List[str]: 
        return len(cls.files(path))
    
    @classmethod
    def encrypt(cls,data: Union[str, bytes], password: str = None, key: str = None,  **kwargs ) -> bytes:
        return c.get_key(key).encrypt(data, password=password,**kwargs)

    @classmethod
    def decrypt(cls, data: Any,  password : str = None, key: str = None, **kwargs) -> bytes:
        return c.get_key(key).decrypt(data, password=password)
    
    
    @classmethod
    def sign(cls, data:dict  = None, key: str = None, **kwargs) -> bool:
        return c.get_key(key).sign(data, **kwargs)
    
    @classmethod
    def verify(cls, auth, key=None, **kwargs ) -> bool:  
        return c.get_key(key).verify(auth, **kwargs)

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

    def set_key(self, key:str, **kwargs) -> None:
        self.key = self.resolve_key(key)
        return self.key
    
    def resolve_key(self, key: str = None) -> str:
        if key != None:
            if isinstance(key, str):
                key =  c.get_key(key)
        else:
            if hasattr(self, 'key'):
                key = self.key
            key = c.key(self.module_name())
        assert hasattr(key, 'ss58_address'), f'Key {key} does not have a sign method'
        return key

    @classmethod
    def is_pwd(cls, module:str = None):
        module = c.module(module) if module != None else cls
        return module.dirpath() == c.pwd()
    
    def __repr__(self) -> str:
        return f'<{self.class_name()}'
    def __str__(self) -> str:
        return f'<{self.class_name()}'
    
    def pull(self):
        return c.cmd('git pull', verbose=True, cwd=c.libpath)
    
    def push(self, msg:str = 'update'):
        c.cmd('git add .', verbose=True, cwd=c.libpath)
        c.cmd(f'git commit -m "{msg}"', verbose=True, cwd=c.libpath)
        return c.cmd('git push', verbose=True, cwd=c.libpath)
    
    # local update  
    @classmethod
    def update(cls,  ):
        c.namespace(update=True)
        c.ip(update=1)
        return {'ip': c.ip(), 'namespace': c.namespace()}
    
    def init_module(self,*args, **kwargs):
        return self.set_config(*args, **kwargs)

    @classmethod
    def utils(cls, search=None):
        utils = c.find_functions(c.rootpath + '/utils')
        if search != None:
            utils = [u for u in utils if search in u]
        return sorted(utils)

    @classmethod
    def get_utils(cls, search=None):
        utils = c.find_functions(c.rootpath + '/utils')
        if search != None:
            utils = [u for u in utils if search in u]
        return sorted(utils)
    
    
    @classmethod
    def num_utils(cls, search=None):
        return len(cls.utils(search))

    cache = {}
    @classmethod
    def util2code(cls, search=None):
        utils = cls.utils()
        util2code = {}
        for f in utils:
            if search != None:
                if search in f:
                    util2code[f] = c.fn_code(f)
        return util2code
    
    @classmethod
    def util2path(cls, search=None):
        utils_paths = cls.utils(search=search)
        util2path = {}
        for f in utils_paths:
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
            setattr(obj, k, partial(wrapper_fn2, fn))
        return {'success': True, 'message': 'added utils'}
    route_cache = None

    @staticmethod
    def get_yaml( path:str=None, default={}, **kwargs) -> Dict:
        '''fLoads a yaml file'''
        import yaml
        path = os.path.abspath(path)
        with open(path, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        return data
    
    @classmethod
    def get_routes(cls):

        if not hasattr(cls, 'routes'):
            routes_path = os.path.dirname(__file__)+ '/routes.json'
            routes =  cls.get_yaml(routes_path)
        else:
            routes = getattr(cls, 'routes')
            if callable(routes):
                routes = routes()
        for util in  c.utils():
            k = '.'.join(util.split('.')[:-1])
            v = util.split('.')[-1]
            routes[k] = routes.get(k , [])
            routes[k].append(v)
        return routes

    @classmethod
    def fn2route(cls):
        routes = cls.get_routes()
        fn2route = {}
        tree = c.tree()
        for module, fns in routes.items():
            is_module = bool( module in tree)
            splitter = '/' if  is_module else '.'
            for fn in fns:
                fn2route[fn] =  module + splitter + fn
        return fn2route
            
    @classmethod
    def add_routes(cls, routes:dict=None, verbose=False, add_utils=True):
        from functools import partial
        """
        This ties other modules into the current module.
        The way it works is that it takes the module name and the function name and creates a partial function that is bound to the module.
        This allows you to call the function as if it were a method of the current module.
        for example
        """
        routes = routes or cls.get_routes()
        t0 = time.time()
        # WARNING : THE PLACE HOLDERS MUST NOT INTERFERE WITH THE KWARGS OTHERWISE IT WILL CAUSE A BUG IF THE KWARGS ARE THE SAME AS THE PLACEHOLDERS
        # THE PLACEHOLDERS ARE NAMED AS module_ph and fn_ph AND WILL UNLIKELY INTERFERE WITH THE KWARGS
        def fn_generator(*args, route, **kwargs):
            def fn(*args, **kwargs):
                try:
                    fn_obj = c.import_object(route)
                except: 
                    module = '.'.join(route.split('.')[:-1])
                    fn = route.split('.')[-1]
                    module = c.module(module)
                    fn_obj = getattr(module, fn)
                    if c.classify_fn(fn_obj) == 'self':
                        fn_obj = getattr(module(), fn)
                if callable(fn_obj):
                    return fn_obj(*args, **kwargs)
                else:
                    return fn_obj
            return fn(*args, **kwargs)
        for module, fns in routes.items():
            for fn in fns: 
                if not hasattr(cls, fn):
                    fn_obj = partial(fn_generator, route=module + '.' + fn) 
                    fn_obj.__name__ = fn
                    setattr(cls, fn, fn_obj)
        latency = time.time() - t0
        return {'success': True, 'msg': 'enabled routes', 'latency': latency}
    
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
        if module == None:
            return c.cmd(f'pytest {c.tests_path}')
        module = module or cls.module_name()

        if c.module_exists( module + '.test'):
            module =  module + '.test'
        module = c.module(module)()
        test_fns = module.test_fns()

        def trial_wrapper(fn, trials=trials):
            def trial_fn(trials=trials):

                for i in range(trials):
                    try:
                        return fn()
                    except Exception as e:
                        print(f'Error: {e}, Retrying {i}/{trials}')
                        cls.c.sleep(1)
                return False
            return trial_fn
        fn2result = {}
        if parallel:
            future2fn = {}
            for fn in test_fns:
                f = c.submit(trial_wrapper(getattr(module, fn)), timeout=timeout)
                future2fn[f] = fn
            for f in cls.as_completed(future2fn, timeout=timeout):
                fn = future2fn.pop(f)
                fn2result[fn] = f.result()
        else:
            for fn in cls.test_fns():
                print(f'testing {fn}')
                fn2result[fn] = trial_wrapper(getattr(cls, fn))()       
        return fn2result
    
    @classmethod
    def is_class(cls, obj):
        return inspect.isclass(obj)
    
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
    def config(cls, module=None, to_munch=True) -> 'Munch':
        '''
        Returns the config
        '''
        module = module or cls
        path = module.config_path()
        if os.path.exists(path):
            config = c.load_yaml(path)
        else:
            config = c.init_kwargs(module)
        if to_munch:
            config =  c.dict2munch(config)
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
    def has_config(cls) -> bool:
        try:
            return os.path.exists(cls.config_path())
        except:
            return False
    
    def update_config(self, config):
        self.config.update(config)
        return self.config

    @classmethod
    def put_json(cls, 
                 path:str, 
                 data:Dict, 
                 meta = None,
                 verbose: bool = False,
                 **kwargs) -> str:
        if meta != None:
            data = {'data':data, 'meta':meta}
        if not path.endswith('.json'):
            path = path + '.json'
        path = cls.resolve_path(path=path)
        # cls.lock_file(path)
        if isinstance(data, dict):
            data = json.dumps(data)
        cls.put_text(path, data)
        return path

    save_json = put_json

    @classmethod
    def map(cls, x, fn):
        if isinstance(x, dict):
            return {k:fn(v) for k,v in x.items()}
        elif isinstance(x, list):
            return [fn(v) for v in x]
        else:
            raise ValueError(f'Cannot map {x}')
        
    def test_map(self):
        x = {'a':1, 'b':2}
        fn = lambda x: x+1
        assert self.map(x, fn) == {'a':2, 'b':3}
        x = [1,2,3]
        assert self.map(x, fn) == [2,3,4]
        return {'success':True, 'message':'map test passed'}
        
    avoid_paths = ['~', '/', './', storage_path]
    @classmethod
    def rm(cls, path,possible_extensions = ['json'], avoid_paths = avoid_paths):
        avoid_paths.append(c.storage_path)
        path = cls.resolve_path(path)
        avoid_paths = [cls.resolve_path(p) for p in avoid_paths] 
        assert path not in avoid_paths, f'Cannot remove {path}'
        if not os.path.exists(path):
            for pe in possible_extensions:
                if path.endswith(pe) and os.path.exists(path + f'.{pe}'):
                    path = path + f'.{pe}'
                    break
        if not os.path.exists(path): 
            return {'success':False, 'message':f'{path} does not exist'}
        if os.path.isdir(path):
            return shutil.rmtree(path)
        if os.path.isfile(path):
            os.remove(path)
        assert not os.path.exists(path), f'{path} was not removed'
        return {'success':True, 'message':f'{path} removed'}
    
    @classmethod
    def glob(cls,  path =None, files_only:bool = True, recursive:bool=True):
        import glob
        path = cls.resolve_path(path)
        if os.path.isdir(path):
            path = os.path.join(path, '**')
        paths = glob.glob(path, recursive=recursive)
        if files_only:
            paths =  list(filter(lambda f:os.path.isfile(f), paths))
        return paths
    
    @classmethod
    def get_json(cls, path:str,default:Any=None, **kwargs):
        path = cls.resolve_path(path)
        if not os.path.exists(path):
            if not path.endswith('.json'):
                path = path + '.json'
        try:
            with open(path, 'r') as file:
                data = json.load(file)
        except Exception as e:
            data = default
        return data
    
    load_json = get_json

    @classmethod
    def path_exists(cls, path:str)-> bool:
        if os.path.exists(path):
            return True
        path = cls.resolve_path(path)
        exists =  os.path.exists(path)
        return exists
    
    file_exists = path_exists

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
    def resolve_path(cls, path:str = None, extension:Optional[str]=None):
        '''
        Abspath except for when the path does not have a
        leading / or ~ or . in which case it is appended to the storage dir
        '''
        if path == None:
            return cls.storage_dir()
        if path.startswith('/'):
            path = path
        elif path.startswith('~') :
            path = os.path.expanduser(path)
        elif path.startswith('.'):
            path = os.path.abspath(path)
        else:
            storage_dir = cls.storage_dir()
            if storage_dir not in path:
                path = os.path.join(storage_dir, path)
        if extension != None and not path.endswith(extension):
            path = path + '.' + extension
        return path
    
    @classmethod
    def abspath(cls, path:str):
        return os.path.abspath(os.path.expanduser(path))
    

    @classmethod
    def put_text(cls, path:str, text:str, key=None) -> None:
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
        return {'success': True, 'path': f'{path}', 'size': len(text)*8}
    
    @classmethod
    def ls(cls, path:str = '', 
           search = None,
           return_full_path:bool = True):
        """
        provides a list of files in the path 

        this path is relative to the module path if you dont specifcy ./ or ~/ or /
        which means its based on the module path
        """
        path = cls.resolve_path(path)
        try:
            ls_files = os.listdir(path)
        except Exception as e:
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
            password: str = None, **kwargs) -> Any:
        '''
        Puts a value in the config
        '''
        encrypt = encrypt or password != None
        
        if encrypt or password != None:
            v = cls.encrypt(v, password=password)

        if not c.jsonable(v):
            v = c.serialize(v)    
        
        data = {'data': v, 'encrypted': encrypt, 'timestamp': time.time()}            
        
        # default json 
        getattr(cls,f'put_{mode}')(k, data)

        data_size = cls.sizeof(v)
    
        return {'k': k, 'data_size': data_size, 'encrypted': encrypt, 'timestamp': time.time()}
    
    @classmethod
    def get(cls,
            k:str, 
            default: Any=None, 
            mode:str = 'json',
            max_age:str = None,
            full :bool = False, 
            update :bool = False,
            password : str = None,
            verbose = False,
            **kwargs) -> Any:
        
        '''
        Puts a value in sthe config, with the option to encrypt it
        Return the value
        '''
        data = getattr(cls, f'get_{mode}')(k,default=default, **kwargs)

        if password != None:
            assert data['encrypted'] , f'{k} is not encrypted'
            data['data'] = c.decrypt(data['data'], password=password)

        data = data or default
        
        if not isinstance(data, dict):
            return default
        if update:
            max_age = 0
        if max_age != None:
            timestamp = 0
            for k in ['timestamp', 'time']:
                if k in data:
                    timestamp = data[k]
                    break
            age = int(time.time() - timestamp)
            if age > max_age: # if the age is greater than the max age
                c.print(f'{k} is too old ({age} > {max_age})', verbose=verbose)
                return default
        
        if not full:
            if isinstance(data, dict):
                if 'data' in data:
                    data = data['data']
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
        return f'{c.storage_path}/{cls.module_name()}'

    @staticmethod
    def sleep(period):
        time.sleep(period) 
    
    def num_files(self, path:str='./')-> int:
        import commune as c
        return len(c.glob(path))
            
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
    def getsource(cls, fn):
        obj = None
        if isinstance(fn, str):
            if c.object_exists(fn):
                obj = c.obj(fn)
            elif c.module_exists(fn):
                obj = c.module(fn)

     
        assert obj != None, f'{fn} is not a function or object'
        return inspect.getsource(obj)
    

    @classmethod
    def fn_code(cls,fn:str, **kwargs) -> str:
        '''
        Returns the code of a function
        '''
        try:
            fn = cls.get_fn(fn)
            code_text = inspect.getsource(fn)
        except Exception as e:
            code_text = None
            raise e
            print(f'Error in getting fn_code: {e}')                    
        return code_text
    
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
    def schema(cls, fn:str = '__init__', **kwargs)->dict:
        '''
        Get function schema of function in cls
        '''
        schema = {}
        fn = cls.get_fn(fn)
        for k,v in dict(inspect.signature(fn)._parameters).items():
            schema[k] = {
                    'default': "_empty"  if v.default == inspect._empty else v.default, 
                    'type': str(type(v.default)).split("'")[1]  if v.default == inspect._empty and v.default != None else v.annotation.__name__
            }
        return schema
    
    @classmethod
    def init_kwargs(cls, obj = None, **kwargs):
        obj = cls.resolve_object(obj)
        fn = getattr(obj, '__init__')
        kwargs =  c.kwargs(fn)
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
    def is_fn(cls, fn:str):
        return '/' in str(fn) or hasattr(cls, str(fn)) or (c.object_exists(fn) and callable(c.obj(fn)))
    
    @classmethod
    def code(cls, module = None, search=None, *args, **kwargs):
        obj = cls.resolve_object(module)
        return inspect.getsource(obj)

    pycode = code
    @classmethod
    def code_hash(cls, module=None,  *args, **kwargs):
        import commune as c
        """
        The hash of the code, where the code is the code of the class (cls)
        """
        return c.hash(c.code(module or cls.module_name(), **kwargs))

    @classmethod
    def kwargs(cls, fn):
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
    def fn_signature(cls, fn) -> dict: 
        '''
        get the signature of a function
        '''
        if isinstance(fn, str):
            fn = getattr(cls, fn)
        return dict(inspect.signature(fn)._parameters)
    
    function_signature = fn_signature

    @classmethod
    def class_functions(cls: Union[str, type], obj=None):
        '''
        Gets the self methods in a class
        '''
        obj = cls.resolve_object(obj)
        functions =  c.get_functions(obj)
        signature_map = {f:c.get_args(getattr(obj, f)) for f in functions}
        return [k for k, v in signature_map.items() if 'cls' in v]

    @classmethod
    def static_functions(cls: Union[str, type], obj=None):
        '''
        Gets the self methods in a class
        '''
        obj = obj or cls
        functions =  c.functions(obj)
        signature_map = {f:c.get_args(getattr(obj, f)) for f in functions}
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
    def get_functions(cls, 
                      obj: Any = None,
                      search = None,
                      splitter_options = ["   def " , "    def "] ,
                      include_hidden = False,
                      **kwargs) -> List[str]:
        '''
        Get a list of functions in a class
        
        Args;
            obj: the class to get the functions from
            include_parents: whether to include the parent functions
            include_hidden:  whether to include hidden functions (starts and begins with "__")
        '''

        obj = cls.resolve_object(obj)
        functions = []
        text = inspect.getsource(obj)
        functions = []
        # just
        for splitter in splitter_options:
            for line in text.split('\n'):
                if f'"{splitter}"' in line:
                    continue
                if line.startswith(splitter):
                    functions += [line.split(splitter)[1].split('(')[0].strip()]

        functions = sorted(list(set(functions)))
        if search != None:
            functions = [f for f in functions if search in f]
        if not include_hidden: 
            functions = [f for f in functions if not f.startswith('__') and not f.startswith('_')]
        return functions
    
    @classmethod
    def functions(cls, obj=None, search = None, include_parents = True):
        obj = cls.resolve_object(obj)
        return c.get_functions(obj=obj, search=search, include_parents=include_parents)

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
 
    def n_fns(self, search = None):
        return len(self.fns(search=search))
    
    fn_n = n_fns
    @classmethod
    def fns(self, search = None, include_parents = True):
        return self.functions(search=search, include_parents=include_parents)
    @classmethod
    def is_property(cls, fn: 'Callable') -> bool:
        '''
        is the function a property
        '''
        fn = c.get_fn(fn)
        return isinstance(fn, property)
    
    @classmethod
    def exists(cls, path:str):
        return os.path.exists(path) or os.path.exists(cls.resolve_path(path))
    @classmethod
    def is_fn(cls, fn, splitters = [':', '/', '.']):
        try:
            if hasattr(cls, fn):
                fn = getattr(cls, fn)
            elif c.object_exists(fn):

                fn = c.obj(fn)
            elif any([s in fn for s in splitters]):
                splitter = [s for s in splitters if s in fn][0]
                module = splitter.join(fn.split(splitter)[:-1])
                fn = fn.split(splitter)[-1]
                fn = getattr(c.get_module(module), fn)
        except Exception as e:
            print('Error in is_fn:', e, fn)
            return False
        return callable(fn)

    @classmethod
    def get_fn(cls, fn:str, splitters=[":", "/"]) -> 'Callable':
        """
        Gets the function from a string or if its an attribute 
        """
        if isinstance(fn, str):
            if hasattr(cls, fn):
                fn2route = cls.fn2route() 
                if fn in fn2route:
                    return c.obj(fn2route[fn])
                return getattr(cls, fn)
            elif c.object_exists(fn):
                    return c.obj(fn)
            
            for splitter in splitters:
                if splitter in fn:
                    module_name= splitter.join(fn.split(splitter)[:-1])
                    fn_name = fn.split(splitter)[-1]
                    if c.module_exists(module_name):
                        module = c.get_module(module_name)
                        return getattr(module, fn_name)
        if callable(fn):
            return fn
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
    
    @classmethod
    def classify_fn(cls, fn):
        if not callable(fn):
            fn = cls.get_fn(fn)
        if not callable(fn):
            return 'cls'
        args = c.get_args(fn)
        if len(args) == 0:
            return 'property'
        if args[0] == 'self':
            return 'self'
        elif args[0] == 'cls':
            return 'class'

        return 'static'
        
    def num_fns(self):
        return len(self.fns())
    
    @classmethod
    def is_dir_module(cls, path:str) -> bool:
        """
        determine if the path is a module
        """
        filepath = cls.name2path(path)
        if path.replace('.', '/') + '/' in filepath:
            return True
        if ('modules/' + path.replace('.', '/')) in filepath:
            return True
        return False
    
    @staticmethod
    def is_imported(package:str) :
        return  bool(package in sys.modules)
    
    @classmethod
    def is_parent(cls, obj=None):
        obj = obj or cls 
        return bool(obj in cls.get_parents())
    
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
    def name2path(cls, 
                    simple:str,
                    extension = '.py',
                    ignore_prefixes = ['', 
                                       'src', 
                                      'commune', 
                                      'commune/module', 
                                      'commune/modules', 
                                      'modules', 
                                      'module',
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
        shortcuts = c.shortcuts
        simple = shortcuts.get(simple, simple)

        if simple.endswith(extension):
            simple = simple[:-len(extension)]

        path = None
        pwd = c.pwd()
        path_options = []
        simple = simple.replace('/', '.')

        # create all of the possible paths by combining the ignore_prefixes with the simple path
        dir_paths = list([pwd+ '/' + x for x in ignore_prefixes]) # local first
        dir_paths += list([c.libpath + '/' + x for x in ignore_prefixes]) # add libpath stuff

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
                    if c.libname in p_text and 'class ' in p_text or '  def ' in p_text:
                        return p   
            if path != None:
                break
        return path


    @classmethod
    def path2name(cls,  
                    path:str, 
                    ignore_prefixes = ['src', 'commune', 'modules', 'commune.modules', 'module'],
                    module_folder_filnames = ['__init__', 'main', 'module'],
                    module_extension = 'py',
                    ignore_suffixes = ['module'],
                    name_map = {'commune': 'module'},
                    compress_path = True,
                    verbose = False,
                    **kwargs
                    ) -> str:
        
        path  = os.path.abspath(path)
        path_filename_with_extension = path.split('/')[-1] # get the filename with extension     
        path_extension = path_filename_with_extension.split('.')[-1] # get the extension
        assert path_extension == module_extension, f'Invalid extension {path_extension} for path {path}'
        path_filename = path_filename_with_extension[:-len(path_extension)-1] # remove the extension
        path_filename_chunks = path_filename.split('_')
        path_chunks = path.split('/')

        if path.startswith(c.libpath):
            path = path[len(c.libpath):]
        else:
            pwd = c.pwd()
            if path.startswith(pwd):
                path = path[len(pwd):]
            else:
                raise ValueError(f'Path {path} is not in libpath {c.libpath} or pwd {pwd}') 
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
            path_chunks = path.split('.')
            simple_path = []
            for chunk in path_chunks:
                if chunk not in simple_path:
                    simple_path += [chunk]
            simple_path = '.'.join(simple_path)
        else:
            simple_path = path
        for prefix in ignore_prefixes:
            prefix += '.'
            if simple_path.startswith(prefix) and simple_path != prefix:
                simple_path = simple_path[len(prefix):]
                c.print(f'Prefix {prefix} in path {simple_path}', color='yellow', verbose=verbose)
        # FILTER SUFFIXES
        for suffix in ignore_suffixes:
            suffix = '.' + suffix
            if simple_path.endswith(suffix) and simple_path != suffix:
                simple_path = simple_path[:-len(suffix)]
                c.print(f'Suffix {suffix} in path {simple_path}', color='yellow', verbose=verbose)
        # remove leading and trailing dots
        if simple_path.startswith('.'):
            simple_path = simple_path[1:]
        if simple_path.endswith('.'):
            simple_path = simple_path[:-1]
        simple_path = name_map.get(simple_path, simple_path)
        return simple_path

    @classmethod
    def find_classes(cls, path='./', depth=8, 
                     class_prefix = 'class ', 
                     file_extension = '.py',
                     class_suffix = ':', **kwargs):
        path = os.path.abspath(path)
        if os.path.isdir(path):
            classes = []
            if depth == 0:
                return []
            for p in c.ls(path):
                if os.path.isdir(p):
                    classes += cls.find_classes(p, depth=depth-1)
                elif p.endswith(file_extension):
                    p_classes =  cls.find_classes(p)
                    classes += p_classes
            return classes
        code = cls.get_text(path)
        classes = []
        file_path = cls.path2objectpath(path)

        for line in code.split('\n'):
            if line.startswith(class_prefix) and line.strip().endswith(class_suffix):
                new_class = line.split(class_prefix)[-1].split('(')[0].strip()
                if new_class.endswith(class_suffix):
                    new_class = new_class[:-1]
                if ' ' in new_class:
                    continue
                classes += [new_class]
        classes = [file_path + '.' + c for c in classes]
        return classes

    @classmethod
    def find_class2functions(cls, path):

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
        
        path = os.path.abspath(path)
        dir_prefixes  = [c.libpath , c.pwd()]
        for dir_prefix in dir_prefixes:
            if path.startswith(dir_prefix):
                path =   path[len(dir_prefix) + 1:].replace('/', '.')
                break
        if path.endswith('.py'):
            path = path[:-3]
        return path.replace('__init__.', '.')
    
    @classmethod
    def objectpath2path(cls, objectpath:str, **kwargs) -> str:
        options  = [c.libpath, c.pwd()]
        for option in options:
            path = option + '/' + objectpath.replace('.', '/') + '.py'
            if os.path.exists(path):
                return path
        raise ValueError(f'Path not found for objectpath {objectpath}')

    @classmethod
    def find_functions(cls, path = './', **kwargs):
        fns = []
        if os.path.isdir(path):
            path = os.path.abspath(path)
            for p in cls.glob(path+'/**/**.py', recursive=True):
                p_fns = c.find_functions(p)
                file_object_path = cls.path2objectpath(p)
                p_fns = [file_object_path + '.' + f for f in p_fns]
                for fn in p_fns:
                    fns += [fn]

        else:
            code = cls.get_text(path)
            for line in code.split('\n'):
                if line.startswith('def ') or line.startswith('async def '):
                    fn = line.split('def ')[-1].split('(')[0].strip()
                    fns += [fn]
        return fns
    
    @classmethod
    def get_objects(cls, path:str = './', depth=10, search=None, **kwargs):
        classes = cls.find_classes(path,depth=depth)
        functions = cls.find_functions(path)

        if search != None:
            classes = [c for c in classes if search in c]
            functions = [f for f in functions if search in f]
        object_paths = functions + classes
        return object_paths
    objs = search =  get_objects
            

    @staticmethod
    def ensure_sys_path():
        if not hasattr(c, 'included_pwd_in_path'):
            c.included_pwd_in_path = False
        pwd = c.pwd()
        if  not c.included_pwd_in_path:
            import sys            
            sys.path.append(pwd)
            sys.path = list(set(sys.path))
            c.included_pwd_in_path = True

    @classmethod
    def import_module(cls, 
                      import_path:str, 
                      ) -> 'Object':
        from importlib import import_module
        c.ensure_sys_path()
        return import_module(import_path)
    
    @classmethod
    def is_module(cls, path:str):
        return os.path.isdir(path) or path.endswith('.py')
    
    @classmethod
    def import_object(cls, key:str, **kwargs)-> Any:
        ''' Import an object from a string with the format of {module_path}.{object}'''
        key = key.replace('/', '.')
        module_obj = c.import_module('.'.join(key.split('.')[:-1]))
        return  getattr(module_obj, key.split('.')[-1])
    
    o = obj = get_obj = import_object

    @classmethod
    def object_exists(cls, path:str, verbose=False)-> Any:
        try:
            c.import_object(path, verbose=verbose)
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
            module = c.shortcuts.get(module, module)
            return os.path.exists(c.name2path(module))
        except Exception as e:
            module_exists =  False

        try:
            module_exists =  bool(c.import_module(module))
        except Exception as e:
            module_exists =  False
        
        return module_exists
    
    @classmethod
    def has_app(cls, module:str, **kwargs) -> bool:
        return cls.module_exists(module + '.app', **kwargs)
    
    
    @classmethod
    def get_path(cls, module:str, **kwargs) -> bool:
        return c.module(module).filepath()
    
    @classmethod
    def objectpath2name(cls, p, 
                        avoid_terms=['modules', 'agents', 'module']):
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
        for avoid_suffix in ['module']:
            if path.endswith('.' + avoid_suffix):
                path = path[:-len(avoid_suffix)-1]
        return path

    @classmethod
    def local_modules(cls, search=None, **kwargs):
        return list(c.local_tree(search=search, **kwargs).keys())
    
    @classmethod
    def lib_tree(cls, depth=10, **kwargs):
        return c.get_tree(c.libpath, depth=depth, **kwargs)
    
    @classmethod
    def core_tree(cls, **kwargs):
        tree =  c.get_tree(c.libpath, **kwargs)
        return {k:v for k,v in tree.items() if 'modules.' not in v}
    @classmethod
    def local_tree(cls , depth=4, **kwargs):
        return c.get_tree(c.pwd(), depth=depth, **kwargs)
    
    @classmethod
    def get_tree(cls, path, depth = 10, max_age=60, update=False, **kwargs):
        tree_cache_path = 'tree/'+os.path.abspath(path).replace('/', '_')
        tree = c.get(tree_cache_path, None, max_age=max_age, update=update)
        if tree == None:
            c.print(f'TREE(max_age={max_age}, depth={depth}, path={path})', color='green')
            class_paths = cls.find_classes(path, depth=depth)
            simple_paths = [cls.objectpath2name(p) for p in class_paths]
            tree = dict(zip(simple_paths, class_paths))
            c.put(tree_cache_path, tree)
        return tree


    _tree = None
    @classmethod
    def tree(cls, search=None,  max_age=60,update=False, **kwargs):
        local_tree = c.local_tree(update=update, max_age=max_age)
        lib_tree = c.lib_tree(update=update, max_age=max_age)
        tree = {**lib_tree, **local_tree}
        if search != None:
            tree = {k:v for k,v in tree.items() if search in k}
        return tree
    
    @classmethod
    def overlapping_modules(cls, search:str=None, **kwargs):
        local_modules = cls.local_modules(search=search)
        core_modules = cls.core_modules(search=search)
        return [m for m in local_modules if m in core_modules]
    
    @classmethod
    def core_modules(cls, search=None, depth=10000, **kwargs):
        object_paths = cls.find_classes(cls.libpath, depth=depth )
        object_paths = [cls.objectpath2name(p) for p in object_paths]
        if search != None:
            object_paths = [p for p in object_paths if search in p]
        return sorted(list(set(object_paths)))
    
    @classmethod
    def get_modules(cls, search=None, **kwargs):
        return list(cls.tree(search=search, **kwargs).keys())
    _modules = None

    def n(self, search=None):
        return len(c.modules(search=search))
    @classmethod
    def modules(cls, 
                search=None, 
                cache=True,
                max_age=60,
                update=False, **extra_kwargs)-> List[str]:
        modules = cls._modules
        modules = cls.get('modules', max_age=max_age, update=update)
        if not cache or modules == None:
            modules =  cls.get_modules(search=None, **extra_kwargs)
            cls.put('modules', modules)
        if search != None:
            modules = [m for m in modules if search in m]     
        return modules
    blocks = modules

    @classmethod
    def has_module(cls, module, path=None):
        path = path or c.libpath
        return module in c.modules()
    
    def new_modules(self, *modules, **kwargs):
        for module in modules:
            self.new_module(module=module, **kwargs)

    def net(self):
        return c.network()

    @classmethod
    def new_module( cls,
                   path : str ,
                   name= None, 
                   base_module : str = 'base', 
                   update=1
                   ):
        path = os.path.abspath(path)
        path = path + '.py' if not path.endswith('.py') else path
        name = name or c.path2name(path)
        base_module = c.module(base_module)
        module_class_name = ''.join([m[0].capitalize() + m[1:] for m in name.split('.')])
        code = base_module.code()
        code = code.replace(base_module.__name__,module_class_name)
        dirpath = os.path.dirname(path)
        assert os.path.exists(path) or update
        if not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        c.put_text(path, code)
        return {'name': name, 'path': path, 'msg': 'Module Created'}
    
    add_module = new_module
    
    @classmethod
    def filter(cls, text_list: List[str], filter_text: str) -> List[str]:
        return [text for text in text_list if filter_text in text]

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
    def repo_url(cls, *args, **kwargs):
        return cls.module('git').repo_url(*args, **kwargs)    

    @classmethod
    def ps(cls, *args, **kwargs):
        return cls.get_module('docker').ps(*args, **kwargs)
 
    @classmethod
    def chown(cls, path:str = None, sudo:bool =True):
        path = cls.resolve_path(path)
        user = os.getenv('USER')
        cmd = f'chown -R {user}:{user} {path}'
        cls.cmd(cmd , sudo=sudo, verbose=True)
        return {'success':True, 'message':f'chown cache {path}'}

    @classmethod
    def chown_cache(cls, sudo:bool = True):
        return cls.chown(c.storage_path, sudo=sudo)
    
    @classmethod
    def get_util(cls, util:str, prefix='commune.utils'):
        path = prefix+'.' + util
        if c.object_exists(path):
            return c.import_object(path)
        else:
            return c.util2path().get(path)

    @classmethod
    def root_key(cls):
        return cls.get_key()

    @staticmethod
    def round(x, sig=6, small_value=1.0e-9):
        import math
        """
        Rounds x to the number of {sig} digits
        :param x:
        :param sig: signifant digit
        :param small_value: smallest possible value
        :return:
        """
        return round(x, sig - int(math.floor(math.log10(max(abs(x), abs(small_value))))) - 1)

    str2hash = hash

    def add_repo(self, repo:str, path:str=None, **kwargs):
        return c.cmd(f'git clone {repo} {path}', **kwargs)

    def add_api_key(self, api_key:str, module=None):
        path = self.get_api_keys_path(module)
        api_keys = self.get(path, [])
        api_keys.append(api_key)
        api_keys = list(set(api_keys))
        self.put(path, api_keys)
        return {'api_keys': api_keys}
    
    def set_api_keys(self, api_keys:str, module:str=None):
        path = self.get_api_keys_path(module)
        api_keys = list(set(api_keys))
        return self.put(path, api_keys)
    
    
    def rm_api_key(self, api_key:str, module:str=None):
        module = module or self.module_name()
        api_keys = self.api_keys(module=module)
        n = len(api_keys)
        if isinstance(api_key, int):
            api_key = api_keys[api_key]
        if api_key in api_keys:
            api_keys.remove(api_key)
            self.set_api_keys(api_keys, module=module)
        else:
            return {'error': f'api_key {api_key} not found'}
        
        assert len(self.api_keys(module)) == n - 1, f'Error removing api key {api_key}'
        return {'api_keys': api_keys}

    def get_api_key(self, module=None):
        return c.choice(self.api_keys(module))
        
    def get_api_keys_path(self, module:str=None):
        module = module or self.module_name()
        return c.resolve_path(f'api_keys/{module}')

    def api_keys(self, module=None):
        path = self.get_api_keys_path(module)
        return c.get(path, [])
    
    def rm_api_keys(self, module=None):
        path = self.get_api_keys_path(module)
        return c.put(path, [])
    
    @classmethod
    def remote_fn(cls, 
                    fn: str='train', 
                    module: str = None,
                    args : list = None,
                    kwargs : dict = None, 
                    name : str =None,
                    refresh : bool =True,
                    interpreter = 'python3',
                    autorestart : bool = True,
                    force : bool = False,
                    cwd = None,
                    **extra_launch_kwargs
                    ):

        kwargs = c.locals2kwargs(kwargs)
        kwargs = kwargs if kwargs else {}
        args = args if args else []
        if 'remote' in kwargs:
            kwargs['remote'] = False
        assert fn != None, 'fn must be specified for pm2 launch'
        kwargs = {'module': module, 'fn': fn, 'args': args, 'kwargs': kwargs}
        name = name or module
        if refresh:
            c.kill(name)
        module = c.module(module)
        kwargs_str = json.dumps(kwargs).replace('"', "'")
        filepath = module.filepath()
        cwd = os.path.dirname(filepath)
        root_filepath = c.module('module').filepath()
        command = f"pm2 start {root_filepath} --name {name} --interpreter {interpreter}"
        if not autorestart:
            command += ' --no-autorestart'
        if force:
            command += ' -f '
        command = command +  f' -- --fn module_fn --kwargs "{kwargs_str}"'
        return c.cmd(command, cwd=cwd)
    
    @staticmethod
    def resolve_extension( filename:str, extension = '.py') -> str:
        if filename.endswith(extension):
                return filename
        return filename + extension
    

    def repo2path(self, search=None):
        repo2path = {}
        for p in c.ls('~/'): 
            if os.path.exists(p+'/.git'):
                r = p.split('/')[-1]
                if search == None or search in r:
                    repo2path[r] = p
        return dict(sorted(repo2path.items(), key=lambda x: x[0]))
    
    def repos(self, search=None):
        return list(self.repo2path(search=search).keys())
    
    def is_repo(self, repo:str):
        return repo in self.repos()

    @classmethod
    def help(cls, *text, module=None,  **kwargs):
        text = ' '.join(map(str, text))
        code = c.code(module or cls.module_name())
        text = f'{code} {text}'
        print('size of text', len(text))
        return c.ask(text, **kwargs)

    def time(self):
        return time.time()
    

    def clone(self, repo:str, path:str=None, **kwargs):
        path = '~/' + repo if path == None else path
        cmd =  f'git clone {repo}'

        return c.cmd(f'git clone {repo} {path}', **kwargs)
    
    def copy_module(self,module:str, path:str):
        code = c.code(module)
        path = os.path.abspath(path)
        import time 
        # put text one char at a time to the file
        # append the char to the code
        c.rm(path)
        for char in code:
            print(char, end='')
            time.sleep(0.000001)
            # append the char to the code one at a time so i can see the progress
            with open(path, 'a') as f:
                f.write(char)
        return {'path': path, 'module': module}
    
    def has_module(self, path:str):
        for path in c.files(path): 
            if path.endswith('.py'):
                return True
    
    @classmethod
    def module2fns(cls, path=None):
        path = path or cls.dirpath()
        tree = c.get_tree(path)
        module2fns = {}
        for m,m_path in tree.items():
            if '.modules.' in m_path:
                continue
            try:
                module2fns[m] = c.module(m).fns()
            except Exception as e:
                pass
        return module2fns
    
    @classmethod
    def fn2module(cls, path=None):
        module2fns = cls.module2fns(path)
        fn2module = {}
        for m in module2fns:
            for f in module2fns[m]:
                fn2module[f] = m
        return fn2module
    

    def install(self, path  ):
        path = path + '/requirements.txt'
        print(path)
        assert os.path.exists(path)
        return c.cmd(f'pip install -r {path}')
    
    def epoch(self, *args, **kwargs):
        return c.run_epoch(*args, **kwargs)
    
c.routes = {
    "vali": [
        "run_epoch",
        "setup_vali",
        "from_module"
    ],
    "py": [
        "envs", 
        "env2cmd", 
        "create_env", 
        "env2path"
        ],
    "cli": [
        "parse_args"
    ],
    "streamlit": [
        "set_page_config",
        "load_style",
        "st_load_css"
    ],
    "docker": [
        "containers",
        "dlogs",
        "images"
    ],
    "client": [
        "call",
        "call_search",
        "connect"
    ],
    "repo": [
        "is_repo",
        "repos"
    ],
    "serializer": [
        "serialize",
        "deserialize",
        "serializer_map",
    ],
    "key": [
        "rename_key",
        "ss58_encode",
        "ss58_decode",
        "key2mem",
        "key_info_map",
        "key_info",
        "valid_ss58_address",
        "valid_h160_address",
        "add_key",
        "from_password",
        "str2key",
        "pwd2key",
        "getmem",
        "mem",
        "mems",
        "switch_key",
        "module_info",
        "rename_kefy",
        "mv_key",
        "add_keys",
        "key_exists",
        "ls_keys",
        "rm_key",
        "key_encrypted",
        "encrypt_key",
        "get_keys",
        "rm_keys",
        "key2address",
        "key_addresses",
        "address2key",
        "is_key",
        "new_key",
        "save_keys",
        "load_key",
        "load_keys",
        "get_signer",
        "encrypt_file",
        "decrypt_file",
        "get_key_for_address",
        "resolve_key_address",
        "ticket"
    ],
    "remote": [
        "host2ssh"
    ],
    "network": [
        "networks",
        "register_server",
        "deregister_server",
        "server_exists",
        "add_server",
        "has_server",
        "add_servers",
        "rm_servers",
        "rm_server",
        "namespace",
        "namespace",
        "infos",
        "get_address",
        "servers",
        "name2address"
    ],
    "app": [
        "start_app",
        "app",
        "apps",
        "app2info",
        "kill_app"
    ],
    "user": [
        "role2users",
        "is_user",
        "get_user",
        "update_user",
        "get_role",
        "refresh_users",
        "user_exists",
        "is_admin",
        "admins",
        "add_admin",
        "rm_admin",
        "num_roles",
        "rm_user"
    ],
    "server": [
        "serve",
        "wait_for_server", 
        "endpoint", 
        "is_endpoint",
        "fleet", 
        "processes", 
        "kill", 
        "kill_many", 
        "kill_all", 
        "kill_all_processes", 
        "logs"
    ],

    "subspace": [
        "transfer_stake",
        "stake_trnsfer",
        "switch",
        "switchnet",
        "subnet",
        "update_module",
        "subnet_params_map",
        "staketo", 
        "network",
        "get_staketo", 
        "stakefrom",
        "get_stakefrom",
        "switch_network",
        "key2balance",
        "subnets",
        "send",
        "my_keys",
        "key2value",
        "transfer",
        "multistake",
        "stake",
        "unstake",
        "register",
        "subnet_params",
        "global_params",
        "balance",
        "get_balance",
        "get_stake",
        "get_stake_to",
        "get_stake_from",
        "my_stake_to",
        "netuid2subnet",
        "subnet2netuid",
        "is_registered",
        "update_subnet",
        "my_subnets", 
        "register_subnet",
        "registered_subnets",
        "registered_netuids"
    ],
    "model.openrouter": [
        "generate",
        "models"
    ],
    "chat": ["ask", "models", "pricing",  "model2info"]
}
c.add_routes()
Module = c # Module is alias of c
Module.run(__name__)


