import commune as c
from typing import *
import os

class Network(c.Module):
    blocktime =  block_time = 8 
    n = 100
    tempo = 60
    blocks_per_day = 24*60*60/block_time
    # the default
    endpoints = ['namespace']
    def __init__(self, network:str='local', tempo=tempo,  path=None, **kwargs):
        self.modules_path = self.resolve_path(path or f'modules_{self.network}')
        self.set_network(network=network, tempo=tempo)

    def set_network(self, network:str, tempo:int=60):
        self.network = network 
        self.tempo = tempo
        return {'network': self.network, 'tempo': self.tempo}
    
    def params(self,*args,  **kwargs):
        return { 'network': self.network, 'tempo' : self.tempo,'n': self.n}

    def modules(self, 
                search=None, 
                max_age=tempo, 
                update=False, 
                features=['name', 'address', 'key'], 
                timeout=8, 
                **kwargs):
        modules = c.get(self.modules_path, max_age=max_age, update=update)
        if modules == None:
            modules = []
            addresses = ['0.0.0.0'+':'+str(p) for p in c.used_ports()]
            futures  = [c.submit(c.call, [s + '/info'], timeout=timeout) for s in addresses]
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
        return {m['name']: m['address'] for m in self.modules(search=search, max_age=max_age, update=update)}

    def register_server(self, name:str, address:str, key:str) -> None:
        data = {'name': name, 'address': address, 'key': key}
        modules = self.modules()
        modules.append(data)
        c.put(self.modules_path, modules)
        return {'success': True, 'msg': f'Block {name}.'}
    
    def register_from_signature(self, signature=None):
        import json
        assert c.verify(signature), 'Signature is not valid.'
        data = json.loads(signature['data'])
        return self.register_server(data['name'], data['address'])
    
    def deregister_server(self, name:str, features=['name', 'key', 'address']) -> Dict:
        modules = self.modules()
        modules = [m for m in modules if not any([m[f] == name for f in features])]
        c.put(self.modules_path, modules)

    def resolve_network(self, network:str) -> str:
        return network or self.network
    
    def resolve_network_path(self, network:str) -> str:
        return self.resolve_path(self.resolve_network(network))
    
    def namespace_exists(self, network:str) -> bool:
        path = self.resolve_network_path( network)
        return os.path.exists(path)
    
    def names(self, *args, **kwargs) -> List[str]:
        return list(self.namespace(*args, **kwargs).keys())
    
    def addresses(self,*args, **kwargs) -> List[str]:
        return list(self.namespace(*args, **kwargs).values())
    
    def servers(self, search=None,  **kwargs) -> List[str]:
        namespace = self.namespace(search=search,**kwargs)
        return list(namespace.keys())
    
    def server_exists(self, name:str, **kwargs) -> bool:
        servers = self.servers(**kwargs)
        return bool(name in servers)
    
    def networks(self, module_prefix:str='network') -> List[str]:
        networks = []
        for m in c.modules(module_prefix):
            if not m.startswith(module_prefix):
                continue
            if m.count('.') == 1:
                network = m.split('.')[-1]
            elif m == module_prefix:
                network = 'local'
            else:
                continue
            networks.append(network)
        networks = sorted(list(set(networks)))
        return networks
              
Network.run(__name__)


