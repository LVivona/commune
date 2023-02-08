

import os
import sys
from copy import deepcopy
from typing import Dict, List, Optional, Union

from commune import Module

class NetworkModule(Module):


    def __init__(self, network:str=None, **kwargs):
        Module.__init__(self,  **kwargs)
        self.set_network(network=network)

    @property
    def network(self):
        network = self.config['network']
        if len(network.split('.')) == 3:
            network = '.'.join(network.split('.')[:-1])
        assert len(network.split('.')) == 2
        return network


    @network.setter
    def network(self, network):
        assert network in self.available_networks
        self.config['network'] = network

    def set_network(self, network:str='local.main.ganache') -> 'Web3':
        network = network if network != None else self.config['network']
        url = self.get_url(network)
        self.network = network
        self.url = url 
        self.web3 = self.get_web3(self.url)
        return self.web3
    
    connect_network = set_network

    def get_web3_from_url(self, url:str):
        from commune.web3.evm.utils import  get_web3
        return get_web3(url)
    get_web3 = get_web3_from_url

    @property
    def networks_config(self):
        return self.config['networks']

    @property
    def networks(self):
        return self.get_networks()

    def get_networks(self):
        return list(self.networks_config.keys())

    @property
    def available_networks(self):
        return self.get_available_networks()


    def get_available_networks(self):
        networks_config = self.networks_config
        subnetworks = []
        for network in self.networks:
            for subnetwork in networks_config[network].keys():
                subnetworks.append('.'.join([network,subnetwork]))
        return subnetworks
    def get_url_options(self, network:str ) -> List[str]:
        assert len(network.split('.')) == 2
        network, subnetwork = network.split('.')
        return list(self.networks_config[network][subnetwork]['url'].keys())

    def get_url(self, network:str='local.main.ganache' ) -> str:
        from commune.utils.dict import dict_get
        
        if len(network.split('.')) == 2:
            url_key = self.get_url_options(network)[0]
            network_key, subnetwork_key = network.split('.')
        elif len(network.split('.')) == 3:
            network_key, subnetwork_key, url_key = network.split('.')
        else:
            raise NotImplementedError(network)

        key_path = [network_key, subnetwork_key, 'url',url_key ]
        return dict_get(self.networks_config, key_path )

if __name__ == '__main__':
    import streamlit as st
    module = NetworkModule.deploy(actor={'name': 'network', 'wrap':True} )
    st.write(module.actor_name)