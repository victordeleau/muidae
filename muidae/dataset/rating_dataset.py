# load and prepare dataset

import pandas as pd
import sys
import math
import logging
from sklearn.model_selection import train_test_split
import torchvision
import torch
import scipy.sparse as sparse
import numpy as np
from random import shuffle
from torch.utils.data.dataset import Dataset as PytorchDataset

# TODO remove first row and column from data (nan, possibly text or something)
np.set_printoptions(threshold=sys.maxsize)

torch.multiprocessing.set_sharing_strategy('file_system')


"""
    load provided dataset inside object, provide useful methods and information
    input
        ...
"""
class RatingDataset(PytorchDataset):

    # pass normalization data to sub-dataset

    def __init__(self, data, name, view="user_view", is_randomized=False, is_sub_dataset=False, is_normalized=False,
            gm=None, um=None, im=None,
            user_index_swap=None, item_index_swap=None,
            userId_map=None, itemId_map=None,
            index_user=None, index_item=None,
            nb_user=None, nb_item=None):

        self.name = name

        self._is_randomized = is_randomized
        self._is_sub_dataset = is_sub_dataset
        self._is_normalized = is_normalized
        self._view = view

        self.iterator_count = 0
        self.column_id, self.row_id = None, None
        self.gm, self.um, self.im = None, None, None


        if not self._is_sub_dataset:

            assert( isinstance(data, pd.DataFrame) )
        
            self.userId_map, self.itemId_map = None, None

            print("\ndf not monotonic")
            print(data)

            data = self._map_index_to_monotonic(data)

            print("\ndf monotonic")
            print(data)

            self.data = sparse.csr_matrix(
                (
                    data.values[:, 2],
                    (data.values[:, 0].astype(int),
                    data.values[:, 1].astype(int))
                )
            )

            print("\nsparse")
            print(self.data)

            self.index_user, self.index_item = data.userId.unique(), data.itemId.unique()

            self.nb_user, self.nb_item = len( self.index_user ), len( self.index_item )

            self.user_index_swap = (np.arange(self.nb_user) if user_index_swap==None else user_index_swap)
            self.item_index_swap = (np.arange(self.nb_item) if item_index_swap==None else item_index_swap)

            print("\nretrieve")
            print( self.data[1,:].todense() )

            # when accessing data from sparse matrix, data[ item_index, user_index ]

        else:

            assert isinstance(data, sparse.csr_matrix)

            self.userId_map, self.itemId_map = userId_map, itemId_map

            self.index_user, self.index_item = index_user, index_item
            
            self.user_index_swap, self.item_index_swap = user_index_swap, item_index_swap

            self.nb_user, self.nb_item = nb_user, nb_item

            self.gm, self.um, self.im = gm, um, im

            self.data = data

        self._io_size = (self.nb_item+1 if self._view == "user_view" else self.nb_user+1 )


    """
        just return the dataset's view
    """
    def get_view(self):

        return self._view


    """
        just return io_size (depends on view)
    """
    def get_io_size(self):

        return self._io_size


    def __iter__(self):

        self.count = 0
        return self


    def __next__(self):

        
        if self._view == "item_view":

            self.iterator_count += 1

            if self.iterator_count > self.nb_item:
                raise StopIteration

            return self.__getitem__(self.iterator_count-1)


        elif self._view == "user_view":

            self.iterator_count += 1

            if self.iterator_count > self.nb_user:
                raise StopIteration

            return self.__getitem__(self.iterator_count-1)

        else:
            return 0


    """
        return size of the dataset (overide required from abstract parent class)
    """
    def __len__(self):
        
        if self._view == "item_view":
            return self.nb_item

        elif self._view == "user_view":
            return self.nb_user

        else:
            return 0


    """
        allow index access of the dataset (overide required from abstract parent class)
        input
            idx: index of the vector we want to grab
    """
    def __getitem__(self, idx):

        if self._view == "item_view":
            
            if idx < 0 or idx > self.nb_item:
                return 0
            else:
                swap_idx = self.item_index_swap[idx]

                # - (self.gm + self.um + self.im[swap_idx])  )

                return np.ravel( self.data[:, swap_idx].todense())

        elif self._view == "user_view":
            
            if idx < 0 or idx > self.nb_user:
                return 0
            else:
                swap_idx = self.user_index_swap[idx]
                
                #tmp = self.data[1, swap_idx].todense()
                #bias = (self.gm + self.um[swap_idx] + self.im)

                return np.ravel( self.data[swap_idx, :].todense())

        else:
            return 0


    """
        remove mean, user and/or item biases and return new Dataset object
        input
            mean:
            user:
            item:
        output:
            dataset: new Dataset object with modified ratings
    """
    def normalize(self, global_mean=True, user_mean=True, item_mean=True):

        self.gm, self.um, self.im = 0, [], []

        if global_mean == True:
            self.gm = self.data.sum() / self.data.getnnz()

        if user_mean == True:
            self.um = np.divide( np.ravel( np.transpose( self.data.sum(axis=1) ) ).astype(float), self.data.getnnz(axis=1) )
        
        if item_mean == True:
            self.im = np.ravel( np.divide( self.data.sum(axis=0).astype(float), self.data.getnnz(axis=0) ) )


    """
        create random swap of row and column indices
        don't randomize and return 0 if self.has_been_randomized==True
        typically if current dataset is a subset of another dataset that has
        been previously randomized.
    """
    def randomize(self):

        if not self.has_been_randomized:

            self.user_index_swap = shuffle(np.arrange(self.nb_user))
            self.item_index_swap = shuffle(np.arrange(self.nb_item))
        
            return self.user_index_swap, self.item_index_swap

        return 0


    """
        map row and column name to monotonic index and save in dict (as string)
        input
            df_data: pandas.DataFrame to process
    """
    def _map_index_to_monotonic(self, df_data):

        temp_dict = {}
        c = 1
        for i in df_data.userId.unique():
            temp_dict[ i ] = c
            c+= 1

        df_data['userId'].replace( temp_dict, inplace = True )

        self.userId_map = dict((str(k), v) for k, v in temp_dict.items())
        
        temp_dict = {}
        c = 1
        for i in df_data.itemId.unique():
            temp_dict[ i ] = c
            c+= 1
        
        df_data['itemId'].replace( temp_dict, inplace = True )

        self.itemId_map = dict((str(k), v) for k, v in temp_dict.items())

        return df_data


    """
        split the dataset into two sub datasets, to create training/validation/testing sets
        input
            split_factor: between 0 and 1, default to 0.8
        output
            tuple of two RatingDataset, subset of this
    """
    def get_split_sets(self, split_factor=0.8, view=None):

        if split_factor >= 1 or split_factor <= 0:
            return 0

        first_dataset, second_dataset = train_test_split(self.data, test_size=1-split_factor)
        first_nb_user, first_nb_item = math.floor( self.nb_user * split_factor), math.floor( self.nb_item * split_factor )
        second_nb_user, second_nb_item = math.floor( self.nb_user * (1-split_factor)), math.floor( self.nb_item * (1-split_factor) )

        return (
                RatingDataset(
                    first_dataset,
                    name=self.name+"_subset",
                    is_randomized=True,
                    is_sub_dataset=True, is_normalized=self._is_normalized,
                    user_index_swap=self.user_index_swap, item_index_swap=self.item_index_swap,
                    userId_map=self.userId_map, itemId_map=self.itemId_map,
                    index_user=self.index_user, index_item=self.index_item,
                    nb_user=first_nb_user, nb_item=first_nb_item,
                    gm=self.gm, um=self.um, im=self.im,
                    view=self._view),
                    
                RatingDataset(
                    second_dataset,
                    name=self.name+"_subset",
                    is_randomized=True,
                    is_sub_dataset=True, is_normalized=self._is_normalized,
                    user_index_swap=self.user_index_swap, item_index_swap=self.item_index_swap,
                    userId_map=self.userId_map, itemId_map=self.itemId_map,
                    index_user=self.index_user, index_item=self.index_item,
                    nb_user=second_nb_user, nb_item=second_nb_item,
                    gm=self.gm, um=self.um, im=self.im,
                    view=self._view)
                )