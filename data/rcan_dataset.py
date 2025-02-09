import re
import os.path
import numpy as np
from PIL import Image, ImageMath
import torchvision.transforms as transforms
import torch
import random

from data.base_dataset import BaseDataset, get_transform
from data.image_folder import make_dataset


class RCANDataset(BaseDataset):
    """
    It requires two directories to host training images from domain A '/path/to/data/trainA'
    and from domain B '/path/to/data/trainB' respectively.
    You can train the model with the dataset flag '--dataroot /path/to/data'.
    Similarly, you need to prepare two directories:
    '/path/to/data/testA' and '/path/to/data/testB' during test time.
    """

    def __init__(self, opt):
        """Initialize this dataset class.

        Parameters:
            opt (Option class) -- stores all the experiment flags; needs to be a subclass of BaseOptions
        """
        BaseDataset.__init__(self, opt)
        self.dir_canonical = os.path.join("/home/robot/andrewk/RobotTeleop/pilot_scripts/canonical_no_shift_priv_info", opt.phase + 'canonical') 
        self.dir_random = os.path.join(opt.dataroot, opt.phase + 'random') 
        #self.dir_real = os.path.join(opt.dataroot, opt.phase + 'real') 
        self.dir_seg = os.path.join(opt.dataroot, opt.phase + 'segmentation') 
        self.dir_depth = os.path.join(opt.dataroot, opt.phase + 'depth') 
        #self.real_states = np.load(os.path.join(opt.dataroot, opt.phase + 'real_states.npy'))

        #self.dir_canonical_pi = '/home/robot/andrewk/RobotTeleop/pilot_scripts/priv_info' # np.load(os.path.join(opt.dataroot, opt.phase + '_canonical_pi.npy'))
        self.dir_canonical_pi = '/home/robot/andrewk/RobotTeleop/pilot_scripts/canonical_no_shift_priv_info'
        self.canonical_pi_paths = [pth for pth in os.listdir(self.dir_canonical_pi) if '.npy' in pth]

        self.canonical_paths = sorted(make_dataset(self.dir_canonical, opt.max_dataset_size))[::-1]
        self.random_paths = sorted(make_dataset(self.dir_random, opt.max_dataset_size))[::-1]
        #self.real_paths = sorted(make_dataset(self.dir_#real, opt.max_dataset_size))
        self.seg_paths = sorted(make_dataset(self.dir_seg, opt.max_dataset_size))[::-1]
        self.depth_paths = sorted(make_dataset(self.dir_depth, opt.max_dataset_size))[::-1]

        self.canonical_size = len(self.canonical_paths)
        self.random_size = len(self.random_paths)
        #self.real_size = len(self.real_paths)
        self.seg_size = len(self.seg_paths)
        self.depth_size = len(self.depth_paths)
        self.index = 0

        #assert self.canonical_size == self.random_size == self.seg_size == self.depth_size, 'Dataset sizes are not the same'

        self.transform_rgb = get_transform(self.opt, grayscale=False)
        self.transform_grayscale = get_transform(self.opt, grayscale=True)

    def __getitem__(self, index):
        """Return a data point and its metadata information.

        Parameters:
            index (int)      -- a random integer for data indexing

        Returns a dictionary that contains A, B, canonical_paths and random_paths 
            A (tensor)       -- an image in the input domain
            B (tensor)       -- its corresponding image in the target domain
            canonical_paths (str)    -- image paths
            random_paths (str)    -- image paths
        """
        #coin = np.random.uniform(0, 1)
        #if coin < 0.7:
        #    index = self.index
        #    self.index += 1
        #real_path = self.real_paths[index % self.real_size]
        #real_img = Image.open(real_path).convert('RGB')
        #real_state = self.real_states[index % self.real_size]

        canonical_path = self.canonical_paths[index % self.canonical_size]  # make sure index is within then range

        seed = re.search(r'\d+', canonical_path[:canonical_path.find('img')]).group()
        index = re.search(r'\d+', canonical_path[canonical_path.find('img'):]).group()
        canonical_pi = np.load(self.dir_canonical_pi + '/canonical_pi' + str(seed) + '.npy')[int(index)]

        sampled_canonical_path = self.canonical_paths[np.random.randint(0, self.canonical_size)]  # make sure index is within then range
        random_path = self.dir_random + '/' + str(seed) + 'img' + index + '.png'
        seg_path = self.dir_seg + '/' + str(seed) + 'img' + index + '.png'
        depth_path = self.dir_depth + '/' + str(seed) + 'img' + index + '.png'

        canonical_img = Image.open(canonical_path).convert('RGB')
        sampled_canonical_img = Image.open(sampled_canonical_path).convert('RGB')
        random_img = Image.open(random_path).convert('RGB')
        seg_img = Image.open(seg_path)
        depth_img = Image.open(depth_path)
    
        # apply image transformation
        canonical = self.transform_rgb(canonical_img)
        sampled_canonical = self.transform_rgb(sampled_canonical_img)
        random = self.transform_rgb(random_img)
        seg = self.transform_grayscale(seg_img)
        depth = self.transform_grayscale(depth_img)
        #real = self.transform_rgb(real_img)


        return {'canonical': canonical, 
                'random': random, 
                'seg': seg, 
                'depth': depth,
                #'real': real, 
                #'real_state': real_state,
                'canonical_path': canonical_path, 
                'random_path': random_path, 
                #'real_path': real_path,
                'sampled_canonical': sampled_canonical,
                'canonical_pi': canonical_pi}

    def __len__(self):
        """
        Return the total number of images in the dataset (real + randomly generated)
        """
        return self.canonical_size # + self.real_size
