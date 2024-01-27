# README

**This repository contains the scripts for the paper "Developer Assignment Method for Software Defects Based on Related Issue Prediction".**

## Scripts

We assign developers for software defects based on realated issue prediction on the Github platform.

First, we provide 20,280 software defects from nine popular open-source projects from inception until 2023. The software defects of nine preojects can be found in (https://github.com/lucaslbc/DARIP/blob/main/DARIP/Code). Researchers can take the 20,280 software defects as a dataset to conduct research.


Second, we provide the available code to verify the effect of our DARIP method. The DARIP method assign developers for software defects based on **three steps**. 


## Step1: Data augment

**[Code/data_augment/data_augment.py](https://github.com/lucas-lbc/DARIP/blob/main/Code/data_augment/data_augment.py)** contains the pre-processing of software defects and the data enhancement processing of samples.


## Step2: Extract features of software defects

For the software defects, we extract text features and developer features respectively.



**[Code/get_bug_feature/get_text_feature/get_text_feature.py](https://github.com/lucas-lbc/DARIP/blob/main/Code/get_bug_feature/get_text_feature/get_text_feature.py)** contains the script to extract text features of software defects.

Meanwhile, the potentially related issue is predicted, and the text information of the related issue is taken as an extension of the text information of the software defect. **[Code/get_bug_feature/get_text_feature/link_recommend.py](https://github.com/lucas-lbc/DARIP/blob/main/Code/get_bug_feature/get_text_feature/link_recommend.py)** contains the script to predict related issues for software defects. 

**[Code/get_bug_feature/get_user_feature/extract_user_feature.py](https://github.com/lucas-lbc/DARIP/blob/main/Code/get_bug_feature/get_user_feature/extract_user_feature.py)** contains the script to extract developer features of software defects.

A heterogeneous collaborative network is constructed based on the three development behaviors of developers: reporting, commenting, and fixing. The meta-paths are defined based on the four collaboration relationships between developers: report–comment, report–fix, comment–comment, and comment–fix. The graph-embedding algorithm metapath2vec is used to extract developer characteristics from the heterogeneous collaborative network.


## Step3: Assign developer

**[Code/classifiter/classifiter.py](https://github.com/IREL-OSS/SCP2022/blob/main/Code/classifiter/classifiter.py)** contains the script to assign developers to software defects.

A fully connected neural network is used to build a classifier, which trains and learns the textual characteristics, developer characteristics, and labels input of software defects in the classifier and uses the ReLU function as the activation function. Since there are cases where there are multiple fixers for a software defect, i.e., multiple labels for a single sample, our classification task belongs to multi-label classification. For this purpose, for the last layer of full connectivity, we use the Sigmoid activation function to calculate the probability of assigning a software defect to each developer category.
