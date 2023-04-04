import streamlit as st
import torch
import os,sys
import asyncio
from transformers import AutoConfig
asyncio.set_event_loop(asyncio.new_event_loop())
import bittensor
import commune
from typing import List, Union, Optional, Dict
from munch import Munch

class BittensorModule(commune.Module):
    wallet_path = os.path.expanduser('~/.bittensor/wallets/')
    def __init__(self,

                wallet:Union[bittensor.wallet, str] = None,
                subtensor: Union[bittensor.subtensor, str] = 'finney',
                create: bool = True,
                register: bool = False
                ):
        
        self.set_subtensor(subtensor=subtensor)
        self.set_wallet(wallet=wallet)
        
        
    @property
    def network_options(self):
        network_options = ['finney','nakamoto', 'nobunaga', '0.0.0.0:9944'] 
        if os.getenv('SUBTENSOR', None) is not None:
            network_options.append(os.getenv('SUBTENSOR'))
            
        return network_options
        
        
        
    def set_subtensor(self, subtensor=None): 
        subtensor_class = self.import_object('commune.bittensor.subtensor')
        if isinstance(subtensor, str):
            if subtensor in self.network_options:
                subtensor = subtensor_class(network=subtensor)
            elif ':' in subtensor:
                subtensor = subtensor_class(chain_endpoint=subtensor)
        
        self.subtensor = subtensor if subtensor else subtensor_class()
        self.metagraph = bittensor.metagraph(subtensor=self.subtensor).load()
        
        return self.subtensor
        
    def set_wallet(self, wallet=None)-> bittensor.Wallet:

        self.wallet = self.get_wallet(wallet)
        self.wallet.create(False, False)
        return self.wallet
    
    @classmethod
    def generate_mnemonic(cls, *args, **kwargs):
        from substrateinterface import Keypair
        return Keypair.generate_mnemonic()
    @classmethod
    def get_wallet(cls, wallet:Union[str, bittensor.wallet]=None) -> bittensor.wallet:
        if isinstance(wallet, str):
            if len(wallet.split('.')) == 2:
                name, hotkey = wallet.split('.')
            elif len(wallet.split('.')) == 1:
                name = bittensor.wallet(name=wallet)
                hotkey = None
            else:
                raise NotImplementedError(wallet)
                
            wallet =bittensor.wallet(name=name, hotkey=hotkey)
        elif isinstance(wallet, type(None)):
            wallet = bittensor.wallet()
        elif isinstance(wallet, bittensor.Wallet):
            wallet = wallet
        else:
            raise NotImplementedError(wallet)

        return wallet 
    
    def resolve_netuid(self, netuid: int = None):
        if netuid is None:
            netuid = 3
        return netuid
    def get_neuron(self, wallet=None, netuid: int = None):
        wallet = self.get_wallet(wallet)
        netuid = self.resolve_netuid(netuid)
        return wallet.get_neuron(subtensor=self.subtensor, netuid=netuid)
    
    
    def get_port(self, wallet=None, netuid: int = None):
        netuid = self.resolve_netuid(netuid)
        return self.get_neuron(wallet=wallet, netuid=netuid ).port

    def get_info(self, wallet=None, key=None, netuid: int = None):
        netuid = self.resolve_netuid(netuid)
        return self.get_neuron(wallet=wallet, netuid = netuid).port
    
    
    @property
    def neuron(self):
        return self.wallet.get_neuron(subtensor=self.subtensor, netuid=3)
        
    
    @classmethod
    def walk(cls, path:str) -> List[str]:
        import os
        path_list = []
        for root, dirs, files in os.walk(path):
            if len(dirs) == 0 and len(files) > 0:
                for f in files:
                    path_list.append(os.path.join(root, f))
        return path_list
    @classmethod
    def list_wallet_paths(cls):
        return cls.ls(cls.wallet_path, recursive=True)
    
    @classmethod
    def list_wallets(cls, registered=True, unregistered=True, output_wallet:bool = True):
        wallet_paths = cls.list_wallet_paths()
        wallets = [p.replace(cls.wallet_path, '').replace('/hotkeys/','.') for p in wallet_paths]

        if output_wallet:
            wallets = [cls.get_wallet(w) for w in wallets]
            
        return wallets
    
    @property
    def default_network(self):
        return self.network_options[0]
    
    @property
    def default_wallet(self):
        return self.list_wallets()[0]
              
    @property
    def network(self):
        return self.subtensor.network
    
    
    def is_registered(self, netuid: int = None):
        netuid = self.resolve_netuid(netuid)
        return self.wallet.is_registered(subtensor= self.subtensor, netuid=  netuid)

    def sync(self):
        return self.metagraph.sync()
    
    @classmethod
    def dashboard(cls):
        st.set_page_config(layout="wide")
        self = cls(wallet='fish', subtensor='nobunaga')

        with st.sidebar:
            self.streamlit_sidebar()
            
        st.write(f'# BITTENSOR DASHBOARD {self.network}')
        # wallets = self.list_wallets(output_wallet=True)
        
        commune.print(commune.run_command('pm2 status'), 'yellow')
        st.write(commune.run_command('pm2 status').split('\n'))
        # st.write(wallets[0].__dict__)
        
        # self.register()
        # st.write(self.run_miner('fish', '100'))

        # self.streamlit_neuron_metrics()
        
    def run_miner(self, 
                coldkey='fish',
                hotkey='1', 
                port=None,
                subtensor = "194.163.191.101:9944",
                interpreter='python3',
                refresh: bool = False):
        
        name = f'miner_{coldkey}_{hotkey}'
        
        wallet = self.get_wallet(f'{coldkey}.{hotkey}')
        neuron = self.get_neuron(wallet)
        
     
        
        try:
            import cubit
        except ImportError:
            commune.run_command('pip install https://github.com/opentensor/cubit/releases/download/v1.1.2/cubit-1.1.2-cp310-cp310-linux_x86_64.whl')
        if port == None:
            port = neuron.port
    
        
        if refresh:
            commune.pm2_kill(name)
            
        
        assert commune.port_used(port) == False, f'Port {port} is already in use'
        command_str = f"pm2 start commune/model/client/model.py --name {name} --time --interpreter {interpreter} --  --logging.debug  --subtensor.chain_endpoint {subtensor} --wallet.name {coldkey} --wallet.hotkey {hotkey} --axon.port {port}"
        # return commune.run_command(command_str)
        st.write(command_str)
          
          
          
    
    def ensure_env(self):

        try:
            import bittensor
        except ImportError:
            commune.run_command('pip install bittensor')
            
        return cubit
    
    
        try:
            import cubit
        except ImportError:
            commune.run_command('pip install https://github.com/opentensor/cubit/releases/download/v1.1.2/cubit-1.1.2-cp310-cp310-linux_x86_64.whl')
            
    

    @property
    def default_subnet(self):
        return 3
        

    def register ( 
            self, 
            wallet = None,
            netuid = None,
            subtensor: 'bittensor.Subtensor' = None, 
            wait_for_inclusion: bool = False,
            wait_for_finalization: bool = True,
            prompt: bool = False,
            max_allowed_attempts: int = 3,
            cuda: bool = True,
            dev_id: Union[int, List[int]] = None,
            TPB: int = 256,
            num_processes: Optional[int] = None,
            update_interval: Optional[int] = 50_000,
            output_in_place: bool = True,
            log_verbose: bool = True,
        ) -> 'bittensor.Wallet':
        """ Registers the wallet to chain.
        Args:
            subtensor( 'bittensor.Subtensor' ):
                Bittensor subtensor connection. Overrides with defaults if None.
            wait_for_inclusion (bool):
                If set, waits for the extrinsic to enter a block before returning true, 
                or returns false if the extrinsic fails to enter the block within the timeout.   
            wait_for_finalization (bool):
                If set, waits for the extrinsic to be finalized on the chain before returning true,
                or returns false if the extrinsic fails to be finalized within the timeout.
            prompt (bool):
                If true, the call waits for confirmation from the user before proceeding.
            max_allowed_attempts (int):
                Maximum number of attempts to register the wallet.
            cuda (bool):
                If true, the wallet should be registered on the cuda device.
            dev_id (int):
                The cuda device id.
            TPB (int):
                The number of threads per block (cuda).
            num_processes (int):
                The number of processes to use to register.
            update_interval (int):
                The number of nonces to solve between updates.
            output_in_place (bool):
                If true, the registration output is printed in-place.
            log_verbose (bool):
                If true, the registration output is more verbose.
        Returns:
            success (bool):
                flag is true if extrinsic was finalized or uncluded in the block. 
                If we did not wait for finalization / inclusion, the response is true.
        """
        # Get chain connection.
        if subtensor == None: subtensor = self.subtensor
        
        netuid = netuid if netuid is not None else self.default_subnet
        dev_id = dev_id if dev_id is not None else self.gpus()
        wallet = wallet if wallet is not None else self.wallet
        
        subtensor.register(
            wallet = wallet,
            netuid = netuid,
            wait_for_inclusion = wait_for_inclusion,
            wait_for_finalization = wait_for_finalization,
            prompt=prompt, max_allowed_attempts=max_allowed_attempts,
            output_in_place = output_in_place,
            cuda=cuda,
            dev_id=dev_id,
            TPB=TPB,
            num_processes=num_processes,
            update_interval=update_interval,
            log_verbose=log_verbose,
        )
        
        return self
  
  
    @classmethod
    def register_loop(cls, *args, **kwargs):
        import commune
        # commune.new_event_loop()
        self = cls(*args, **kwargs)
        wallets = self.list_wallets()
        for wallet in wallets:
            # print(wallet)
            self.set_wallet(wallet)
            self.register(dev_id=commune.gpus())
            
            
    @classmethod
    def create_wallets_from_dict(cls, 
                                 wallets: Dict,
                                 overwrite: bool = True):
        
        '''
        wallet_dict = {
            'coldkey1': { 'hotkeys': {'hk1': 'mnemonic', 'hk2': 'mnemonic2'}},
        '''
        wallets = {}
        for coldkey_name, hotkey_dict in wallet_dict.items():
            bittensor.wallet(name=coldkey_name).create_from_mnemonic(coldkey, overwrite=overwrite)
            wallets = {coldkey_name: {}}
            for hotkey_name, mnemonic in hotkey_dict.items():
                wallet = bittensor.wallet(name=coldkey_name, hotkey=hotkey_name).regenerate_hotkey(mnemonic=mnemonic, overwrite=overwrite)
                wallets[coldkey_name] = wallet
    @classmethod
    def create_wallets(cls, 
                       wallets: Union[List[str], Dict] = [f'ensemble.{i}' for i in range(3)],
                       coldkey_use_password:bool = False, 
                       hotkey_use_password:bool = False
                       ):
        
        if isinstance(wallets, list):
            for wallet in wallets:
                assert (wallet, str), 'wallet must be a string'
                cls.get_wallet(wallet)
                cls.create_wallet(coldkey=ck, hotkey=hk, coldkey_use_password=coldkey_use_password, hotkey_use_password=hotkey_use_password)   
                    
    @classmethod
    def create_wallet(cls, 
                      wallet: str = 'default.default',
                       coldkey_use_password:bool = False, 
                       hotkey_use_password:bool = False,
                       mnemonic: str= None,
                       seed: str = None
                       ) :
        wallet = cls.get_wallet(wallet)
        
<<<<<<< HEAD
        return  wallet.create(coldkey_use_password=coldkey_use_password, 
                              hotkey_use_password=hotkey_use_password)
=======
        if mnemonic:
            raise NotImplementedError
        if seed:
            raise NotImplementedError
        
        wallet = bittensor.wallet(name=coldkey, hotkey=hotkey)
        return  wallet.create(coldkey_use_password=coldkey_use_password, hotkey_use_password=hotkey_use_password)     
            
            
>>>>>>> 2617a1662ed3363c86e78cbd5dac293f75e6dfdf
            
    @classmethod
    def register_wallet(
                        cls, 
                        wallet='default.default',
                        dev_id: Union[int, List[int]] = None, 
                        create: bool = True,
                        **kwargs
                        ):
        cls(wallet=wallet).register(dev_id=dev_id, **kwargs)

<<<<<<< HEAD
              
=======


>>>>>>> 2617a1662ed3363c86e78cbd5dac293f75e6dfdf
    @classmethod  
    def sandbox(cls):
        
        st.write(cls.list_wallet_paths())
        # for i in range(processes_per_gpus):
        #     for dev_id in gpus:
        #         cls.launch(fn='register_wallet', name=f'reg.{i}.gpu{dev_id}', kwargs=dict(dev_id=dev_id), mode='ray')
        
        # print(cls.launch(f'register_{1}'))
        # self = cls(wallet=None)
        # self.create_wallets()
        # # st.write(dir(self.subtensor))
        # st.write(self.register(dev_id=0))
        
# Streamlit Landing Page    
    selected_wallets = []
    def streamlit_sidebar(self):
        wallets_list = self.list_wallets(output_wallet=False)
        wallet = st.selectbox(f'Select Wallets ({wallets_list[0]})', wallets_list, 0)
        self.set_wallet(wallet)
        
        network_options = self.network_options
        network = st.selectbox(f'Select Network ({network_options[0]})', self.network_options, 0)
        self.set_subtensor(subtensor=network)
        
        sync_network = st.button('Sync the Network')
        if sync_network:
            self.sync()
             
    def streamlit_neuron_metrics(self, num_columns=3):
        with st.expander('Neuron Stats', True):
            cols = st.columns(num_columns)
            if self.is_registered():
                neuron = self.neuron
                if neuron == None:
                    return 
                for i, (k,v) in enumerate(neuron.__dict__.items()):
                    
                    if type(v) in [int, float]:
                        cols[i % num_columns].metric(label=k, value=v)
                st.write(neuron.__dict__)
            else:
                st.write(f'## {self.wallet} is not Registered on {self.subtensor.network}')

    @classmethod
    def streamlit(cls):
        st.set_page_config(layout="wide")
        self = cls(wallet='ensemble_0.0', subtensor='nobunaga')

        with st.sidebar:
            self.streamlit_sidebar()
            
            
        st.write(f'# BITTENSOR DASHBOARD {self.network}')

        self.streamlit_neuron_metrics()
        
        
if __name__ == "__main__":
    BittensorModule.run()


    



