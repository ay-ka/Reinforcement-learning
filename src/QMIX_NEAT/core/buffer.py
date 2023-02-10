
import numpy as np
import random
import torch
from torch.multiprocessing import Manager
from collections import namedtuple
from src.QMIX_NEAT.core import utils
import pdb


class Buffer:
    
    def __init__(self, capacity : int = 10000, episode_limit : int = 25):
        
        """
        buffer to store transition.

        Args:
            capacity: number of transition can be stored.
            
        other parameters:
            episode_record: number of transition which are stored up to now
            store_index: index indicating where new transition should be stored in buffer (buffer index)

        Returns:
            no return --> initialize buffer

        """
        
        self.buffer_capacity = capacity
        self.episode_record = 0
        self.store_index = 0
        self.episode_limit = episode_limit
        self.buffer = dict()
        self.experience = namedtuple("Experience", field_names=["obs","done", "reward", "action_onehot"])
        
        #initialize buffer
        for episode in range(self.buffer_capacity):
            self.buffer[episode] = []
            for limit in range(self.episode_limit):
                self.buffer[episode].append(self.experience(0,0,0,0))
        
         
    def add(self, trajectory):
           
        #store transition on buffer
        self.buffer[self.store_index][:] = trajectory
        
        #update store index
        self.episode_record += 1
        self.store_index = self.episode_record % self.buffer_capacity
        
        
    def sample(self, batch_size) -> dict:
        
        """
        sample batch of transition from buffer

        Args:
            batch_size : number of transition to select when sampling.
        Returns:
           batch: dictionary of transition returned as batch
        """
        keys = {}; batch = {}
        buffer_index = []
        keys_index = 0
        if self.episode_record < self.buffer_capacity:
            indicies = list(self.buffer.keys())[0 : self.episode_record]
            if self.episode_record < batch_size:
                batch_indicies = np.random.choice(indicies, size = self.episode_record, replace=False)
            else:
                batch_indicies = np.random.choice(indicies, size = batch_size, replace=False)        
        else:
            indicies = list(self.buffer.keys())
            batch_indicies = np.random.choice(indicies, size = batch_size, replace=False)
        
        #take experience batch
        for index, targeted_index in enumerate(batch_indicies):
            key = "transition_" + str(targeted_index) + "_idx_" + str(index)
            batch[key] = self.buffer[targeted_index] #befor it was indexs 
            keys[keys_index] = key
            keys_index += 1
            buffer_index.append(targeted_index)
        batch = self.PreperationBatch(batch) 
        return keys, batch, buffer_index
    
    
    def PreperationBatch(self, input_batch : dict) -> list:
            
        """
         
        create seprated batch from transitions (obs_batch, state_batch, .....)

        Args:
        
            input_batch: batch sampled from buffer (dictionary of named tuples)

        Returns:
        
            output_batch: batch sampled from buffer with targeted modifications
                                                   (seprated batches --> obs_batch or next_obs_batch and ....)

        """
        
        obs_batch  =  []
        
        action_onehot_batch,  done_batch, reward_batch = [], [], []
        
        
        #create batches as inputs to insert to train method

        for index, episode in input_batch.items():
            
            obs, action_onehot, done, reward = [], [], [], []
            
            for transition in episode:

                obs.append(transition.obs)

                reward.append(transition.reward)

                done.append(transition.done)

                action_onehot.append(transition.action_onehot)
                
            concatenateor = utils.NumpyConcatenate(obs, action_onehot, reward, done)   
            
            obs_batch.append([concatenateor.__next__()])
            
            action_onehot_batch.append([concatenateor.__next__()])
            
            reward_batch.append([concatenateor.__next__()])
            
            done_batch.append([concatenateor.__next__()])
              
            
        concatenateor = utils.NumpyConcatenate(obs_batch, action_onehot_batch,
                                              reward_batch, done_batch)
        
        output_batch = []
        
        while True:
            
            try:
            
                output_batch.append( concatenateor.__next__() )
                
            except:
                
                break

        return output_batch

    def __len__(self):
        # print(f"store index is {self.store_index} \n")
        # print(f"total record is {self.episode_record} \n")
        return self.store_index





