import os
import csv
import json
import random
import torch
from preprocess_text import vectorlize_string
from transformers import BertModel, BertConfig, BertTokenizer

'''
#数据增强的步骤
step1. 先处理噪声，把样本量为1的类别删除，并把原始数据按比例切分出训练集和测试集，这里的数据集只保存了的bug的编号
step2. 对训练集中的数据做数据增强，生成新的数据
step3. 针对数据增强后的数据提取文本特征和人员特征
step4. 生成可以输入模型的训练集
'''

def getCsvFile(csvfile):
    buginfolist = []
    csv.field_size_limit(500 * 1024 * 1024)
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            buginfolist.append(row)
        csv_f.close()
    return buginfolist


def step1_filterNoises(csvfile):
    repo = ""
    buginfolist = getCsvFile(csvfile)
    fixerDict = {}
    for buginfo in buginfolist:
        repo = buginfo["Repo"]
        fixerlist = buginfo["Fixers"].split(";")
        for fixer in fixerlist:
            if fixer not in fixerDict:
                fixerDict[fixer] = [buginfo]
            else:
                fixerDict[fixer].append(buginfo)

    filterFixerList = []
    for fixer_temp in fixerDict:
        fixerlist_temp = fixerDict[fixer_temp]
        if len(fixerlist_temp) == 1:
            filterFixerList.append(fixer_temp)


    classDict = {}
    for fixer_temp_0 in fixerDict:
        buginfolist_temp = fixerDict[fixer_temp_0]
        if len(buginfolist_temp) == 1:
            continue

        buginfolist_new = []
        for buginfo_temp in buginfolist_temp:
            fixerlist_temp1 = buginfo_temp["Fixers"].split(";")
            jiaoji_list = list(set(filterFixerList) & set(fixerlist_temp1))
            if len(jiaoji_list) == 0:
                buginfolist_new.append(buginfo_temp)
            else:
                if len(fixerlist_temp1) == 1:
                    continue
                else:
                    fixerlist_new = []
                    for fixer_temp_1 in fixerlist_temp1:
                        if fixer_temp_1 not in jiaoji_list:
                            fixerlist_new.append(fixer_temp_1)
                    if len(fixerlist_new) > 0:
                        fixerstr_new = ";".join(fixerlist_new)
                        buginfo_temp_new = buginfo_temp.copy()
                        buginfo_temp_new["Fixers"] = fixerstr_new
                        buginfolist_new.append(buginfo_temp_new)
        classDict[fixer_temp_0] = buginfolist_new


    print("项目%s的数据集中共有%d个类别" % (repo, len(classDict)))

    #根据类别给修复人员添加索引
    classmap = {}
    idx = 0
    for classname in classDict:
        name_Index = "idx_" + str(idx) + "_" + classname
        classmap[classname] = name_Index
        idx += 1

    classDict_new = {}
    for classname_temp in classDict:
        new_classname_temp = classmap[classname_temp]
        class_list_temp = classDict[classname_temp]
        new_class_list = []
        for class_dict_temp in class_list_temp:
            old_class_list = class_dict_temp["Fixers"].split(";")
            new_class_list_sub = []
            for old_class_name in old_class_list:
                new_class_name = classmap[old_class_name]
                new_class_list_sub.append(new_class_name)
            new_class_dict = class_dict_temp.copy()
            new_class_dict["Fixers"] = new_class_list_sub
            new_class_list.append(new_class_dict)
        classDict_new[new_classname_temp] = new_class_list

    train_ratio = 0.8
    train_dataset_list_num = []
    test_dataset_list_num = []

    for fixer in classDict_new:
        max = len(classDict_new[fixer])
        train_num = int(max * train_ratio)
        if max == 2:
            train_num = 1
        train_list = getRandomNumList(max, train_num)
        fixer_dict_list = classDict_new[fixer]
        k = 0
        for fixer_dict in fixer_dict_list:
            if k in train_list:
                train_dataset_list_num.append(fixer_dict)
            else:
                test_dataset_list_num.append(fixer_dict)
            k += 1

    train_bugnum = []
    test_bugnum = []
    for tempdict_train in train_dataset_list_num:
        bugnum_train = tempdict_train["IssueNum"]
        train_bugnum.append(bugnum_train)

    for tempdict_test in test_dataset_list_num:
        bugnum_test = tempdict_test["IssueNum"]
        if bugnum_test not in test_bugnum:
            test_bugnum.append(bugnum_test)


    jiaoji_list1 = list(set(train_bugnum) & set(test_bugnum))


    train_dataset_list_num_new = []
    recordBugList = []
    for tempdict_train1 in train_dataset_list_num:
        bugnum_train1 = tempdict_train1["IssueNum"]
        if bugnum_train1 not in recordBugList:
            train_dataset_list_num_new.append(tempdict_train1)
            recordBugList.append(bugnum_train1)

    test_dataset_list_num_new = []
    recordBugList_test = []
    for tempdict_test1 in test_dataset_list_num:
        bugnum_test1 = tempdict_test1["IssueNum"]
        if bugnum_test1 not in jiaoji_list1 and bugnum_test1 not in recordBugList_test:
            test_dataset_list_num_new.append(tempdict_test1)
            recordBugList_test.append(bugnum_test1)

    bugsum = len(train_dataset_list_num_new) + len(test_dataset_list_num_new)
    print("项目%s的数据集中共有%d个样本" % (repo, bugsum))

    return train_dataset_list_num_new, test_dataset_list_num_new

def step2_dataAugment(train_dataset_raw, p):
    classDict = {}
    for tempBugdict in train_dataset_raw:
        fixerlist_temp = tempBugdict["Fixers"]
        for fixer_temp in fixerlist_temp:
            if fixer_temp not in classDict:
                classDict[fixer_temp] = [tempBugdict]
            else:
                classDict[fixer_temp].append(tempBugdict)

    maxClassNum = 0
    for fixer_temp1 in classDict:
        fixerdictlist_temp = classDict[fixer_temp1]
        if len(fixerdictlist_temp) > maxClassNum:
            maxClassNum = len(fixerdictlist_temp)

    threshold = int(maxClassNum * p)
    classDict_new = {}
    augmentBugDict = {}
    for fixer_temp2 in classDict:
        fixerdictlist_temp2 = classDict[fixer_temp2]
        fixerdictlist_temp2_new = fixerdictlist_temp2.copy()
        currentLen = len(fixerdictlist_temp2)
        if currentLen < threshold:
            minus = threshold - currentLen
            random_list = getRandomNumList(currentLen, minus)
            for randomNum in random_list:
                bugInfo = fixerdictlist_temp2[randomNum].copy()
                text_raw = bugInfo["Title_Description"]
                text_new = dataAugment(text_raw)
                bugInfo["Title_Description"] = text_new
                bug = bugInfo["IssueNum"]

                if bug not in augmentBugDict:
                    i = 0
                    augmentBugDict[bug] = i
                else:
                    i = augmentBugDict[bug] + 1
                    augmentBugDict[bug] = i

                bugInfo["IssueNum"] = bug + "_" + str(i)
                fixerdictlist_temp2_new.append(bugInfo)
        classDict_new[fixer_temp2] = fixerdictlist_temp2_new

    train_dataset_new = []
    for fixer_temp3 in classDict_new:
        fixerdictlist_temp3 = classDict_new[fixer_temp3]
        train_dataset_new += fixerdictlist_temp3

    return train_dataset_new

def step3_extractFeacture(repo, train_dataset_numlist, test_dataset_numlist):
    #获取人员特征
    user_config_file = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/userFeature.config"
    with open(user_config_file, 'r') as userf:
        userdata = json.load(userf)
        userf.close()

    datasetlist = [train_dataset_numlist, test_dataset_numlist]
    i = 0
    train_dataset_list = []
    test_dataset_list = []

    #收集所有文本统一提取特征

    for tempDictlist in datasetlist:
        i += 1
        bugTextDict = {}
        for tempDict in tempDictlist:
            bugNum = tempDict["IssueNum"]
            text = tempDict["Title_Description"]
            bugTextDict[bugNum] = text

        bugTextFeatDict = extractTextFeacture(bugTextDict)

        temp_dataset_list = []
        for tempDict1 in tempDictlist:
            temp_dict = {}

            bugNum1 = tempDict1["IssueNum"]
            temp_dict["bugNum"] = bugNum1

            fixerlist = tempDict1["Fixers"]
            # fixerlist = fixerstr.split(";")
            temp_dict["fixer"] = fixerlist

            bugNum1_raw = bugNum1
            if "_" in bugNum1:
                bugNum1_raw = bugNum1.split("_")[0]
            if bugNum1_raw not in userdata:
                temp_dict["user_feature"] = [0.00 for i in range(768)]
            else:
                temp_dict["user_feature"] = userdata[bugNum1_raw]

            textFeat = bugTextFeatDict[bugNum1]
            temp_dict["text_feature"] = textFeat

            temp_dataset_list.append(temp_dict)

        if i == 1:
            train_dataset_list = temp_dataset_list
        else:
            test_dataset_list = temp_dataset_list

    outfile_train = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/train_list_dataset_rawData_Augment_p8n5.config"
    outfile_test = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/test_list_dataset_rawData_Augment_p8n5.config"
    with open(outfile_train, 'w') as trainf:
        json.dump(train_dataset_list, trainf)
        trainf.close()

    with open(outfile_test, 'w') as testf:
        json.dump(test_dataset_list, testf)
        testf.close()
    return


def extractTextFeacture(bugTextDict):
    outDict = {}
    sum = len(bugTextDict)
    finishNum = []
    using_bert = True
    if using_bert:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device('cpu')
        UNCASED = "F:/research_3/code/bert_base_uncased"
        bert_uncased_model = BertModel.from_pretrained(UNCASED).to(device)
        # bert_uncased_config = BertConfig.from_pretrained(UNCASED)
        bert_uncased_tokenizer = BertTokenizer.from_pretrained(UNCASED)

    for bug in bugTextDict:
        finishNum.append(bug)
        print("当前进度：%d / %d, 正在提取缺陷%s的文本特征" % (len(finishNum), sum, bug))
        textInfo = bugTextDict[bug]
        text = vectorlize_string(textInfo)
        input_ids = bert_uncased_tokenizer(text, truncation=True, max_length=512)
        input_ids = torch.tensor(input_ids['input_ids']).unsqueeze(0).to(device)
        with torch.no_grad():
            pooled_output = bert_uncased_model(input_ids)
            pooled_output = pooled_output[1].to("cuda")
        outDict[bug] = [float(x) for x in pooled_output[0]]

    return outDict



def getRepoInfo(csvfile):
    buglist = []
    csv.field_size_limit(500 * 1024 * 1024)
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            bugdict = {}
            bugdict['Repo'] = row['Repo']
            bugdict['IssueNum'] = row['IssueNum']
            if row['IssueNum'] == "zshihang;jingxu97":
                print("zshihang;jingxu97")
            bugdict['Title_Description'] = row['Title_Description']
            bugdict['Fixers'] = row['Fixers'].split(";")
            buglist.append(bugdict)
        csv_f.close()
    return buglist



def getFixersNum(buglist):
    fixerdict = {}
    for bugdict in buglist:
        fixerlist = bugdict['Fixers']
        for fixer in fixerlist:
            if fixer not in fixerdict:
                fixerdict[fixer] = 1
            else:
                fixerdict[fixer] += 1

    max = 0
    for fixer in fixerdict:
        count = fixerdict[fixer]
        if count > max:
            max = count

    return max, fixerdict

def getSampleByFixers(buglist):
    sampleDict = {}
    for bugdict in buglist:
        fixerlist = bugdict['Fixers']
        for fixer in fixerlist:
            if fixer not in sampleDict:
                sampleDict[fixer] = [bugdict]
            else:
                sampleDict[fixer].append(bugdict)

    max = 0
    for fixer in sampleDict:
        count = len(sampleDict[fixer])
        if count > max:
            max = count

    return max, sampleDict

def traverseSamples(max, fixerdict, p):
    threshold = int(max * p)
    outdict = {}
    augmentBugDict = {}
    for fixer in fixerdict:
        fixerlist = fixerdict[fixer]
        fixerlist_new = []
        for tempdict in fixerlist:
            tempdict_new = tempdict.copy()
            # bugnum = tempdict["IssueNum"]
            # # if bugnum == "13424":
            # #     print(bugnum)
            templist = tempdict["Fixers"]
            tempstr = ";".join(templist)
            tempdict_new["Fixers"] = tempstr
            fixerlist_new.append(tempdict_new)
        outdict[fixer] = fixerlist_new
        if len(fixerlist) >= threshold:
            continue
        #需要数据增强
        addIdx = getRandomNumList(len(fixerlist), threshold - len(fixerlist))
        for idx in addIdx:
            bugInfo = fixerlist[idx].copy()
            text_raw = bugInfo["Title_Description"]
            # if text_raw == "":
            #     print(text_raw)
            text_new = dataAugment(text_raw)
            bugInfo["Title_Description"] = text_new
            bug = bugInfo["IssueNum"]

            if bug not in augmentBugDict:
                i = 0
                augmentBugDict[bug] = i
            else:
                i = augmentBugDict[bug] + 1
                augmentBugDict[bug] = i

            bugInfo["IssueNum"] = bug + "_" + str(i)
            fixerstr = ";".join(bugInfo["Fixers"])
            bugInfo["Fixers"] = fixerstr
            outdict[fixer].append(bugInfo)

    # outdict_new = {}
    # for temp in outdict:
    #     templist = outdict[temp]
    #     for subdict in templist:
    #         sublist = subdict["Fixers"]
    #         for fix in sublist:
    #             if fix not in outdict_new:
    #                 outdict_new[fix] = [subdict]
    #             else:
    #                 outdict_new[fix].append(subdict)

    return outdict


def dataAugment(text_raw):
    isHuanhang = False
    if "\n" in text_raw:
        isHuanhang = True
        text_list = text_raw.split("\n") #段落中交换句子用换行
    else:
        text_list = text_raw.split(" ") #句子中交换单词用空格
    n = 5
    max = len(text_list)
    for i in range(n):
        i = random.randint(0, max-1)
        text_i = text_list[i]
        j = random.randint(0, max-1)
        text_j = text_list[j]
        while text_i == text_j:
            j = random.randint(0, max - 1)
            text_j = text_list[j]
        text_list[i] = text_j
        text_list[j] = text_i
    CharRu = " "
    if isHuanhang:
        CharRu= "\n"
    text_new = CharRu.join(text_list)
    return text_new



def getRandomNumList(max, addnum):
    retlist = []
    if max == 1:
        retlist = [0] * addnum
    else:
        count = 0
        while count < addnum:
            random_idx = random.randint(0, max-1)
            retlist.append(random_idx)
            count += 1

    return retlist


def outputDataAugmentFile(indict, outputcsvfile):
    with open(outputcsvfile, 'w', encoding='utf-8', newline='') as output_csvf:
        fnames = ['Repo', 'IssueNum', 'Fixers', 'Title_Description']
        writer = csv.DictWriter(output_csvf, fieldnames=fnames)
        writer.writeheader()
        for fixer in indict:
            fixerlist = indict[fixer]
            for subdict in fixerlist:
                writer.writerow(subdict)
        output_csvf.close()
    return


def overWriteCsvfile(csvfile):
    csv.field_size_limit(500 * 1024 * 1024)
    bugslist = []
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            if row["Fixers"][-1] == ";":
                row["Fixers"] = row["Fixers"][0:-1]
            if row["Labels"][-1] == ";":
                row["Labels"] = row["Labels"][0:-1]
            if len(row["Commentators"]) > 0:
                if row["Commentators"][-1] == ";":
                    row["Commentators"] = row["Commentators"][0:-1]
            if len(row["Label_adders"]) > 0:
                if row["Label_adders"][-1] == ";":
                    row["Label_adders"] = row["Label_adders"][0:-1]
            if len(row["Label_removers"]) > 0:
                if row["Label_removers"][-1] == ";":
                    row["Label_removers"] = row["Label_removers"][0:-1]
            if len(row["Assigns"]) > 0:
                if row["Assigns"][-1] == ";":
                    row["Assigns"] = row["Assigns"][0:-1]
            if len(row["Unassigns"]) > 0:
                if row["Unassigns"][-1] == ";":
                    row["Unassigns"] = row["Unassigns"][0:-1]
            if len(row["Closer"]) > 0:
                if row["Closer"][-1] == ";":
                    row["Closer"] = row["Closer"][0:-1]
            bugslist.append(row)
        csv_f.close()

    outputfile = csvfile[0:-4] + "_new.csv"
    with open(outputfile, 'w', encoding='utf-8', newline='') as output_csvf:
        fnames = ['Repo', 'IssueNum', 'Title_Description', 'Fixers', 'Labels', 'Created_at', 'Closed_at', 'Creator',
                  'Commentators', 'Label_adders', 'Label_removers', 'Assigns', 'Unassigns', 'Closer', 'Links']
        writer = csv.DictWriter(output_csvf, fieldnames=fnames)
        writer.writeheader()
        for outdict in bugslist:
            writer.writerow(outdict)
        output_csvf.close()
    return

if __name__ == "__main__":
    dirpath = "F:/research_3/data/zzz_csv_data/data-csv/"
    repo_list = [
        'ant-design',
        'electron',
        'flutter',
        'kubernetes',
        'next.js',
        'PowerToys',
        'tensorflow',
        'terminal',
        'TypeScript'
        # 'vscode'
    ]
    for repo in repo_list:
        csvfile = dirpath + repo + ".csv"
        print("处理项目：", repo)
        train_dataset_list_num, test_dataset_list_num = step1_filterNoises(csvfile)
        p = 0.8
        train_dataset_list_num_new = step2_dataAugment(train_dataset_list_num, p)

        step3_extractFeacture(repo, train_dataset_list_num_new, test_dataset_list_num)
        # buglist = getRepoInfo(csvfile)
        # max, sampleDict = getSampleByFixers(buglist)
        # p = 0.6
        # outdict = traverseSamples(max, sampleDict, p)
        # outputfile = csvfile[0:-4] + "_augment.csv"
        # outputDataAugmentFile(outdict, outputfile)
        # print("输出文件成功：", outputfile)
