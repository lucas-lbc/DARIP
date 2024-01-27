import time
import json
import torch
from torch import nn
from d2l import torch as d2l
from matplotlib import pyplot as plt
from torchvision import transforms
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import tqdm

class MyData(Dataset):
    def __init__(self, dataset_file):
        bugs = []
        bugfixerlist = []

        #train_dataset_file = configPath + "/train_list_dataset.config"
        #test_dataset_file = configPath + "/test_list_dataset.config"

        with open(dataset_file, 'r') as datasetf:
            dataset_list = json.load(datasetf)
            datasetf.close()

        for temp_bugdict in dataset_list:
            if temp_bugdict["fixer"] not in bugfixerlist:
                bugfixerlist.append(temp_bugdict["fixer"])
            bugfixer = temp_bugdict["fixer"].split("_")[1]
            fixer_num = int(bugfixer)
            fixer_tensor = torch.tensor(fixer_num)
            bugTensor_text = torch.tensor(temp_bugdict["text_feature"])
            # # print(bugTensor_text.shape)
            # # print(bugTensor_text)

            bugTensor_user = torch.tensor(temp_bugdict["user_feature"])
            bugTensor = torch.cat((bugTensor_text, bugTensor_user), dim=0)

            #print(bugTensor.shape)

            # print(bugTensor.shape)
            # print(bugTensor)
            bugs.append((bugTensor, fixer_tensor))#bugTensor

        self.bugs = bugs
        self.labelnum = len(bugfixerlist)

    def __len__(self):
        return len(self.bugs)

    def __getitem__(self, index):
        return self.bugs[index]

    # def getClassNum(self):
    #     return self.classnum


class MyData_MultiLabels(Dataset):
    def __init__(self, dataset_file, labelnum=-1):
        bugs = []

        with open(dataset_file, 'r') as datasetf:
            dataset_list = json.load(datasetf)
            datasetf.close()

        #统计类型，即共有多少个修复人员
        bugfixerlist = []
        for temp_bugdict in dataset_list:
            temp_list = temp_bugdict["fixer"]
            for fixer in temp_list:
                if fixer not in bugfixerlist:
                    bugfixerlist.append(fixer)
        if labelnum == -1:
            labelnum = len(bugfixerlist)

        #转换label的格式
        for temp_bugdict in dataset_list:
            labels_list = temp_bugdict["fixer"]
            labels_idx_list = [0.0]*labelnum
            for label in labels_list:
                idx = int(label.split("_")[1])
                labels_idx_list[idx] = 1.0

            label_tensor = torch.tensor(labels_idx_list)
            bugTensor_text = torch.tensor(temp_bugdict["text_feature"])
            bugTensor_user = torch.tensor(temp_bugdict["user_feature"])
            bugTensor = torch.cat((bugTensor_text, bugTensor_user), dim=0)
            bugs.append((bugTensor, label_tensor))



        self.bugs = bugs
        self.labelnum = labelnum
        self.datalen = len(dataset_list)

    def __len__(self):
        return len(self.bugs)

    def __getitem__(self, index):
        return self.bugs[index]

    # def getClassNum(self):
    #     return self.labelnum


def init_weight(m):
    if type(m) == nn.Linear:
        nn.init.normal_(m.weight, std=0.01)




if __name__ == "__main__":
    #filter_config("F:/research_3/data/zzz_csv_data/data-csv/ant-design")

    # device = torch.device("cuda")

    path = "F:/research_3/data/zzz_csv_data/data-csv/"

    repo_list = [
        'ant-design',
        'electron',
        'flutter',
        'next.js',
        'PowerToys',
        'terminal',
        'TypeScript',
        'tensorflow',
        'kubernetes'
        # 'vscode'
    ]


    for repo in repo_list:

        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        datasource = ["rawData_Augment_p8n5"]#, "filterNoises" "rawData" "textExtension_all"
        for source in datasource:

            batch_size = 32

            # print(source)
            # 1.加载数据集
            train_dataset_file = path + repo + "/train_list_dataset_" + source + ".config"#_rawData filterNoises
            # train_dataset_file = "F:/research_3/data/zzz_csv_data/data-csv/flutter" + "/train_list_dataset_filterNoises.config"#_rawData filterNoises
            # train_data = MyData(train_dataset_file)
            train_data = MyData_MultiLabels(train_dataset_file)
            train_iter = DataLoader(train_data, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=False)

            train_datalen = train_data.datalen
            labelnum = train_data.labelnum
            print("项目：%s 数据：%s 类别数：%d" % (repo, source, labelnum))
            # #测试
            # for bugs, labels in train_iter:
            #     print(bugs.shape)
            #     print(labels.shape)

            test_dataset_file = path + repo + "/test_list_dataset_" + source + ".config"  # _rawData filterNoises
            # test_dataset_file = "F:/research_3/data/zzz_csv_data/data-csv/flutter" + "/test_list_dataset_filterNoises.config"#_rawData filterNoises
            # test_data = MyData(test_dataset_file)
            test_data = MyData_MultiLabels(test_dataset_file, labelnum=labelnum)
            test_iter = DataLoader(test_data, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=False)


            # 2.定义模型[batch_size, channel, H, W]
            net = nn.Sequential(
                nn.Flatten(),  # 起到平铺的作用[batch_size, channel*H*W]
                nn.Linear(2*768, 1024),
                nn.ReLU(),
                nn.Linear(1024, 256),
                nn.ReLU(),
                nn.Linear(256, labelnum),
                # nn.Softmax()
                nn.Sigmoid()
            )

            # net1 = nn.Sigmoid


            # 3.初始化模型参数
            net.apply(init_weight)

            # 4.定义损失函数
            # loss = nn.CrossEntropyLoss(reduction='none')
            # loss = nn.BCELoss(reduction='none')

            # 5.定义优化器
            trainer = torch.optim.SGD(net.parameters(), lr=0.05)

            # epochs_dataset = 50
            # num_epochs = int((epochs_dataset * train_datalen) / batch_size)
            # print("需要迭代的次数：", num_epochs)
            num_epochs = 2000


            # for bugs, labels in train_iter:
            #     print(bugs.shape)
            #     print(labels.shape)
            # for bugs, labels in test_iter:
            #     print(bugs.shape)
            #     print(labels.shape)

            # d2l.train_ch3(net, train_iter, test_iter, loss, num_epochs, trainer)
            # d2l.train_ch6(net, train_iter, test_iter, num_epochs, lr=0.001, device=d2l.try_gpu())
            # d2l.train_ch6_topk(net, train_iter, test_iter, num_epochs, lr=0.001, device=d2l.try_gpu(), topk_list=[1, 3, 5, 10], path=path, repo=repo, source=source)
            d2l.train_ch6_topk_multiLabel(net, train_iter, test_iter, num_epochs, lr=0.05, device=d2l.try_gpu(), topk_list=[1, 3, 5, 10], path=path, repo=repo, source=source)
            #d2l.train_ch13(net, train_iter, test_iter, loss, trainer, num_epochs, devices=d2l.try_all_gpus())
            # plt.show()
            plt.close()
