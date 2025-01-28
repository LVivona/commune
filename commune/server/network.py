from typing import *
import os
import commune as c
class Network(c.Module):
    min_stake = 0
    block_time = 8 
    n = 100
    tempo = 60
    endpoints = ['namespace']
    def __init__(self, network:str='local', tempo=tempo,  path=None, **kwargs):
        self.set_network(network=network, tempo=tempo, path=path)

    def set_network(self, network:str, tempo:int=60, path=None, **kwargs):
        self.network = network 
        self.tempo = tempo
        self.modules_path = self.resolve_path(path or f'{self.network}/modules')
        return {'network': self.network, 'tempo': self.tempo, 'modules_path': self.modules_path}
    
    def params(self,*args,  **kwargs):
        return { 'network': self.network, 'tempo' : self.tempo,'n': self.n}

    def modules(self, 
                search=None, 
                max_age=tempo, 
                update=False, 
                features=['name', 'url', 'key'], 
                timeout=8, 
                **kwargs):
        modules = c.get(self.modules_path, max_age=max_age, update=update)
        if modules == None:
            modules = []
            urls = ['0.0.0.0'+':'+str(p) for p in c.used_ports()]
            futures  = [c.submit(c.call, [s + '/info'], timeout=timeout) for s in urls]
            try:
                for f in c.as_completed(futures, timeout=timeout):
                    data = f.result()
                    if all([k in data for k in features]):
                        modules.append({k: data[k] for k in features})
            except Exception as e:
                c.print('Error getting modules', e)
                modules = []
            c.put(self.modules_path, modules)
        if search != None:
            modules = [m for m in modules if search in m['name']]
        return modules

    def namespace(self, search=None,  max_age:int = tempo, update:bool = False, **kwargs) -> dict:
        return {m['name']: '0.0.0.0' + ':' + m['url'].split(':')[-1] for m in self.modules(search=search, max_age=max_age, update=update)}

    def add_server(self, name:str, url:str, key:str) -> None:
        data = {'name': name, 'url': url, 'key': key}
        modules = self.modules()
        modules.append(data)
        c.put(self.modules_path, modules)
        return {'success': True, 'msg': f'Block {name}.'}
    
    def rm_server(self, name:str, features=['name', 'key', 'url']) -> Dict:
        modules = self.modules()
        modules = [m for m in modules if not any([m[f] == name for f in features])]
        c.put(self.modules_path, modules)

    def resolve_network(self, network:str) -> str:
        return network or self.network
    
    def names(self, *args, **kwargs) -> List[str]:
        return list(self.namespace(*args, **kwargs).keys())
    
    def urls(self,*args, **kwargs) -> List[str]:
        return list(self.namespace(*args, **kwargs).values())
    
    def servers(self, search=None,  **kwargs) -> List[str]:
        namespace = self.namespace(search=search,**kwargs)
        return list(namespace.keys())
    
    def server_exists(self, name:str, **kwargs) -> bool:
        servers = self.servers(**kwargs)
        return bool(name in servers)

    def infos(self, *args, **kwargs) -> Dict:
        return self.modules(*args, **kwargs)

