import csv
import json
import time
from scipy import spatial
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
'''
#为每个缺陷推荐潜在的相关问题
步骤如下：
1. 收集每个缺陷的文本特征
2. 针对每个缺陷问题，分别计算该缺陷与历史缺陷之间的余弦相似度
3. 选择相似度最高的历史缺陷（或者选择相关性最高且大于阈值（0.5）的历史缺陷）
'''

def time2Timestamp(timestr):
    timestr = timestr[0:10] + ' ' + timestr[11:-1]
    timeArray = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(timeArray))
    return timestamp

def getTextFeatureForBug(repo, topk):
    dirpath = "F:/research_3/data/zzz_csv_data/data-csv/"
    configfile = dirpath + repo + "/log_v2.config"
    with open(configfile, 'r') as textf:
        textdata = json.load(textf)
        textf.close()

    bugInfoDict = {}
    buglist = []
    csvfile = dirpath + repo + ".csv"
    csv.field_size_limit(500 * 1024 * 1024)
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            bugs = row['IssueNum']
            buglist.append(int(bugs))

            infoDict = {}
            infoDict["Repo"] = row["Repo"]
            infoDict["IssueNum"] = bugs
            infoDict["Title_Description"] = row["Title_Description"]
            infoDict["Fixers"] = row["Fixers"]
            infoDict["Created_at"] = row["Created_at"]
            infoDict["Closed_at"] = row["Closed_at"]
            bugInfoDict[bugs] = infoDict
        csv_f.close()

    buglist.sort()
    oldbugDict = {}
    for idx in range(len(buglist)):
        if idx == 0:
            continue
            # oldbugDict[bugNum] = []
        bugNum = str(buglist[idx])
        bugNumInfoDict = bugInfoDict[bugNum]
        createdtime = bugNumInfoDict["Created_at"]
        createdtimeStamp = time2Timestamp(createdtime)
        oldbuglist = []
        for j in range(idx):
            oldbugNum = str(buglist[j])
            tempInfoDict = bugInfoDict[oldbugNum]
            old_createdtime = tempInfoDict["Closed_at"]#Closed_at
            old_createdtimeStamp = time2Timestamp(old_createdtime)
            if old_createdtimeStamp < createdtimeStamp:
                intervalTime = createdtimeStamp - old_createdtimeStamp
                if intervalTime < 7776000:#3个月的时间
                    oldbuglist.append(oldbugNum)
        oldbugDict[bugNum] = oldbuglist


    lastBugDict = {}
    for eachBug in bugInfoDict:
        currentBugFeat = textdata[eachBug]
        if eachBug in oldbugDict:
            tempoldBuglist = oldbugDict[eachBug]
            cosValList = []
            tempoldbuglist = []
            for tempoldbug in tempoldBuglist:
                oldbugFeat = textdata[tempoldbug]
                cos_sim = calCosSiml_scipy(currentBugFeat, oldbugFeat)
                # cos_sim2 = calCosSiml_numpy(currentBugFeat, oldbugFeat)
                # cos_sim3 = calCosSiml_sklearn(currentBugFeat, oldbugFeat)
                cosValList.append(cos_sim)
                tempoldbuglist.append(tempoldbug)
            #选相关性最大的历史缺陷
            topk_buglist = []
            topk_vallist = []

            iterCount = topk
            if len(cosValList) < topk:
                iterCount = len(cosValList)

            m = 0
            while m < iterCount:
                max_value = max(cosValList)
                max_idx = cosValList.index(max_value)
                max_bug = tempoldbuglist[max_idx]
                topk_buglist.append(max_bug)
                topk_vallist.append(str(max_value))
                del cosValList[max_idx]
                del tempoldbuglist[max_idx]
                m += 1

            realk = len(topk_buglist)
            sumFeac = currentBugFeat
            for i in range(realk):
                cosval_i = topk_vallist[i]
                bug_i = topk_buglist[i]
                bugFeac_i = textdata[bug_i]
                sumFeac = [(x * float(cosval_i) + y) for x, y in zip(bugFeac_i, sumFeac)]

                # sumFeac += cosval_i * bugFeac_i
            # avgFeac = sumFeac / (realk + 1)
            avgFeac = [x/(realk + 1) for x in sumFeac]
            lastBugDict[eachBug] = avgFeac

        else:
            lastBugDict[eachBug] = currentBugFeat

    outconfigfile = dirpath + repo + "/log_linkTop" + str(topk) + ".config"
    with open(outconfigfile, 'w') as outf:
        json.dump(lastBugDict, outf)
        outf.close()

    return

def feacWeighting(list1, list2, cosim):
    retlist = []
    length = len(list1)
    for i in range(length):
        val1 = list1[i]
        val2 = list2[i]
        ret = val1 * cosim + val2
        retlist.append(ret)
    return retlist


def calCosSiml_scipy(vec1, vec2):
    cosSimVal = 1 - spatial.distance.cosine(vec1, vec2)
    return cosSimVal

# def calCosSiml_numpy(vec1, vec2):
#     arr1 = np.array(vec1)
#     arr2 = np.array(vec2)
#     cosSimVal = arr1.dot(arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2))
#     return cosSimVal
#
# def calCosSiml_sklearn(vec1, vec2):
#     arr1 = np.array(vec1)
#     arr2 = np.array(vec2)
#     cosSimVal = cosine_similarity(arr1.reshape(1, -1), arr2.reshape(1, -1))
#     return cosSimVal

def outPut(oldBugDict, repo, dirpath):
    csvfile = dirpath + repo + ".csv"
    csv.field_size_limit(500 * 1024 * 1024)
    buglist = []
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            buglist.append(row)
        csv_f.close()

    outlist = []
    for bugdict in buglist:
        bugdict_new = bugdict.copy()
        bugNum = bugdict["IssueNum"]
        if bugNum in oldBugDict:
            infoList = oldBugDict[bugNum]
            topk_buglist = infoList[0]
            topk_vallist = infoList[1]
            bugdict_new["RLink"] = ";".join(topk_buglist)
            bugdict_new["Cos_sim"] = ";".join(topk_vallist)#str(infoList[1])
        del bugdict_new["Labels"], bugdict_new["Label_adders"], bugdict_new["Label_removers"], bugdict_new["Assigns"], bugdict_new["Unassigns"], bugdict_new["Creator"], bugdict_new["Closer"]
        outlist.append(bugdict_new)
    outputfile = csvfile[0:-4] + "_RLink_1.csv"
    with open(outputfile, 'w', encoding='utf-8', newline='') as output_csvf:
        fnames = ['Repo', 'IssueNum', 'Title_Description', 'Fixers', 'Created_at', 'Closed_at', 'Creator',
                  'Commentators', 'Links', 'RLink', 'Cos_sim']
        writer = csv.DictWriter(output_csvf, fieldnames=fnames)
        writer.writeheader()
        for outdict in outlist:
            writer.writerow(outdict)
        output_csvf.close()

    return


def textExtension(csvfile):
    bugLinkdict = {}
    bugInfoDict = {}
    csv.field_size_limit(500 * 1024 * 1024)
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            bugs = row['IssueNum']

            infoDict = {}
            infoDict["Repo"] = row["Repo"]
            infoDict["IssueNum"] = bugs
            infoDict["Title_Description"] = row["Title_Description"]
            infoDict["Fixers"] = row["Fixers"]
            infoDict["Created_at"] = row["Created_at"]
            infoDict["Closed_at"] = row["Closed_at"]
            infoDict["RLink"] = row["RLink"]
            bugInfoDict[bugs] = infoDict

            if row['RLink'] != "":
                linkNum = row['RLink']
                bugLinkdict[bugs] = linkNum

        csv_f.close()

    linknum = 0
    for bug in bugLinkdict:
        # targetrepo = bugInfoDict[bug]["Repo"]
        # bug_origin_createdat = bugInfoDict[bug]["Created_at"]
        # bug_origin_createdat_stamp = time2Timestamp(bug_origin_createdat)
        linkBug = bugLinkdict[bug]
        bugInfoDict[bug]["Title_Description"] += "\n" + bugInfoDict[linkBug]["Title_Description"]
        linknum += 1
            # bug_target_closedat = bugInfoDict[targetbug]["Closed_at"]
            # bug_target_closedat_stamp = time2Timestamp(bug_target_closedat)
            # if bug_target_closedat_stamp < bug_origin_createdat_stamp:
            #     bugInfoDict[bug]["Title_Description"] += "\n" + bugInfoDict[targetbug]["Title_Description"]
            #     linknum += 1

    fullnum = len(bugInfoDict)
    outcsvfile = csvfile[0:-4] + "_v2.csv"
    with open(outcsvfile, "w", encoding="utf-8", newline="") as outcsvf:
        fnames = ['Repo', 'IssueNum', 'Fixers', "Created_at", "Closed_at", "Title_Description", "RLink"]
        writer = csv.DictWriter(outcsvf, fieldnames=fnames)
        writer.writeheader()
        for bugnum in bugInfoDict:
            infoDict = bugInfoDict[bugnum]
            writer.writerow(infoDict)
        outcsvf.close()
    print("处理项目：", repo)
    print("缺陷总数：%d, link数量：%d, 比例：%f" % (fullnum, linknum, linknum/fullnum))
    return

def textLength(repo):
    all = 0
    len512 = 0
    csvfile = dirpath + repo + ".csv"
    csv.field_size_limit(500 * 1024 * 1024)
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            body = row["Title_Description"]
            if len(body) >= 512:
                len512 += 1
            all += 1
        csv_f.close()
    print("项目：%s中文本长度大于512的占比为：%f" % (repo, len512/all))


# def textExtension_v0(oldBugDict, repo, dirpath):
#     csvfile = dirpath + repo + ".csv"
#     csv.field_size_limit(500 * 1024 * 1024)
#     buglist = []
#     with open(csvfile, 'r', errors='ignore') as csv_f:
#         readers = csv.DictReader(csv_f)
#         for row in readers:
#             buglist.append(row)
#         csv_f.close()
#
#     bugInfoDict = {}
#     for bugdict in buglist:
#         bugnum = bugdict["IssueNum"]
#         if bugnum in oldBugDict:
#             bugdict_new = bugdict.copy()
#             infolist = oldBugDict[bugnum]
#             linkbug = infolist[0][0]
#             bugdict_new["Title_Description"] += "\n" + bugInfoDict[linkbug]["Title_Description"]
#
#         else:
#             bugInfoDict[bugnum] = bugdict
#
#     # outlist = []
#     # for bugdict in buglist:
#     #     bugdict_new = bugdict.copy()
#     #     bugNum = bugdict["IssueNum"]
#     #     if bugNum in oldBugDict:
#     #         infoList = oldBugDict[bugNum]
#     #         topk_buglist = infoList[0]
#     #         topk_vallist = infoList[1]
#     #         bugdict_new["RLink"] = ";".join(topk_buglist)
#     #         bugdict_new["Cos_sim"] = ";".join(topk_vallist)#str(infoList[1])
#     #     del bugdict_new["Labels"], bugdict_new["Label_adders"], bugdict_new["Label_removers"], bugdict_new["Assigns"], bugdict_new["Unassigns"], bugdict_new["Creator"], bugdict_new["Closer"]
#     #     outlist.append(bugdict_new)
#
#
#
#
#
#
#     for bugNum in oldBugDict
#     bugNum = oldBugDict["IssueNum"]
#     if bugNum in oldBugDict:
#         infoList = oldBugDict[bugNum]
#         topk_buglist = infoList[0]
#         topk_vallist = infoList[1]
#         bugdict_new["RLink"] = ";".join(topk_buglist)
#         bugdict_new["Cos_sim"] = ";".join(topk_vallist)  # str(infoList[1])
#
#
#     bugLinkdict = {}
#     bugInfoDict = {}
#     csv.field_size_limit(500 * 1024 * 1024)
#     with open(csvfile, 'r', errors='ignore') as csv_f:
#         readers = csv.DictReader(csv_f)
#         for row in readers:
#             bugs = row['IssueNum']
#
#             infoDict = {}
#             infoDict["Repo"] = row["Repo"]
#             infoDict["IssueNum"] = bugs
#             infoDict["Title_Description"] = row["Title_Description"]
#             infoDict["Fixers"] = row["Fixers"]
#             infoDict["Created_at"] = row["Created_at"]
#             infoDict["Closed_at"] = row["Closed_at"]
#             infoDict["RLink"] = row["RLink"]
#             bugInfoDict[bugs] = infoDict
#
#             if row['RLink'] != "":
#                 linkNum = row['RLink']
#                 bugLinkdict[bugs] = linkNum
#
#         csv_f.close()
#
#     linknum = 0
#     for bug in bugLinkdict:
#         # targetrepo = bugInfoDict[bug]["Repo"]
#         # bug_origin_createdat = bugInfoDict[bug]["Created_at"]
#         # bug_origin_createdat_stamp = time2Timestamp(bug_origin_createdat)
#         linkBug = bugLinkdict[bug]
#         bugInfoDict[bug]["Title_Description"] += "\n" + bugInfoDict[linkBug]["Title_Description"]
#         linknum += 1
#             # bug_target_closedat = bugInfoDict[targetbug]["Closed_at"]
#             # bug_target_closedat_stamp = time2Timestamp(bug_target_closedat)
#             # if bug_target_closedat_stamp < bug_origin_createdat_stamp:
#             #     bugInfoDict[bug]["Title_Description"] += "\n" + bugInfoDict[targetbug]["Title_Description"]
#             #     linknum += 1
#
#     fullnum = len(bugInfoDict)
#     outcsvfile = csvfile[0:-4] + "_v2.csv"
#     with open(outcsvfile, "w", encoding="utf-8", newline="") as outcsvf:
#         fnames = ['Repo', 'IssueNum', 'Fixers', "Created_at", "Closed_at", "Title_Description", "RLink"]
#         writer = csv.DictWriter(outcsvf, fieldnames=fnames)
#         writer.writeheader()
#         for bugnum in bugInfoDict:
#             infoDict = bugInfoDict[bugnum]
#             writer.writerow(infoDict)
#         outcsvf.close()
#     print("处理项目：", repo)
#     print("缺陷总数：%d, link数量：%d, 比例：%f" % (fullnum, linknum, linknum/fullnum))
#     return

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
        print("处理项目：", repo)
        getTextFeatureForBug(repo, topk=1)
        getTextFeatureForBug(repo, topk=3)
        getTextFeatureForBug(repo, topk=5)
        #outPut(oldBugDict, repo, dirpath)
        #csvfile = dirpath + repo + "_RLink_1.csv"
        #textExtension(csvfile)

        # textLength(repo)

