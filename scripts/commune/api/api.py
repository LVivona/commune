
import commune 
from commune import Module

from fastapi import FastAPI
from pydantic import BaseModel
from typing import *     
import json 
import torch
from commune.api.types import *

class APIModule(Module):
    module_tree = {}
    def __init__(self, demo_mode:bool = True):
        if demo_mode:
            self.set_demo_mode_params()
        self.module_name = 'module'

    def predict(self, data: dict= {}):
        return f"Prediction for {self.name}: {data}"

    def list_modules(self):
        
        modules = list(self.module_tree.values())
        return modules
    
    @property
    def module_list(self): 
        return self.list_modules()
    
    def get_module(self, name:str):
        module = self.module_tree.get(name)
        return module
        
    def resolve_module(self, module: Any = None):
        
        module = module if module else self
        
        return module


    async def call_api(self, fn:str, module:str = None, kwargs: str = None, args:str = None):
            
        kwargs = {} if kwargs == None else json.loads(kwargs)
        args = [] if args == None else json.loads(args)
        
        module = self.resolve_module(module=module)

        fn_obj =  getattr(module, fn)
        kwargs = kwargs if kwargs != None else {}
        args = args if args != None else []
        print(args, kwargs, 'DEBUG')
        if callable(fn_obj):
            return fn_obj(*args, **kwargs)
        else: 
            return fn_obj
    @classmethod
    def api(cls, *cls_args, **cls_kwargs):
        app = FastAPI()
        self = cls(*cls_args, **cls_kwargs)

        @app.get("/", tags=["health Check"])
        async def name():
            return 'commxune'
        @app.post("/list_modules")
        async def list_modules():
            return self.list_modules()

        @app.post("/get_module")
        async def get_module(name:str):
            return self.get_module(name)
        
        @app.post("/fn/{fn}")
        async def call_api(fn:str, module:str = None, kwargs: str = None, args:str = None):
            return self.call_api(fn=fn, module=module, kwargs=kwargs, args=args)

        from fastapi.middleware.cors import CORSMiddleware
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app
    
    def set_demo_mode_params(self):
        for m in ['gpt2', 'gpt3', 'gpt4', 'gpt5']:
            self.module_tree['model.'+m] =  Model(name=m).state

        for m in ['gpt2', 'gpt3', 'gpt4', 'gpt5']:
            self.module_tree['dataset.'+m] =  Dataset(name=m).state


app = APIModule.api()




    
