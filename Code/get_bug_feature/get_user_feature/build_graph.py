import os, csv, time
import networkx as nx

class Build_Graph:

    def __init__(self, datapath, repo):
        self.datapath = datapath
        self.repo = repo
        self.csvfile = datapath + "/" + repo + '.csv'

    def getUserNum(self):
        bugs_list = []
        user_list = []
        # edge_list = []
        csvfile = self.csvfile
        csv.field_size_limit(500 * 1024 * 1024)
        with open(csvfile, 'r', errors='ignore') as csv_f:
            readers = csv.DictReader(csv_f)
            for row in readers:
                bugs = row['IssueNum']
                bugs_list.append(bugs)
                '''收集Fixers'''
                fixers_str = row['Fixers']
                my_fixerslist = fixers_str[0:-1].split(';')
                for fix in my_fixerslist:
                    if fix not in user_list:
                        user_list.append(fix)
                    # edge = bugs + ' ' + fix + ' ' + 'fix'
                    # edge_list.append(edge)
                '''收集Commentators'''
                comments_str = row['Commentators']
                if len(comments_str) > 0:
                    my_commentlist = comments_str[0:-1].split(';')
                    for comment in my_commentlist:
                        if comment not in user_list:
                            user_list.append(comment)
                        # edge = bugs + ' ' + comment + ' ' + 'comment'
                        # edge_list.append(edge)
                '''收集Creator'''
                creator = row['Creator']
                if creator not in user_list:
                    user_list.append(creator)
                # edge = bugs + ' ' + creator + ' ' + 'create'
                # edge_list.append(edge)
            csv_f.close()
        return user_list


    def getInput(self):
        path = self.datapath
        repo = self.repo
        csvfile = self.csvfile
        print('读取文件：', csvfile)

        '''如果项目文件夹不存在，则创建文件夹'''
        repodir = path + '/' + repo
        isrepoexist = os.path.exists(repodir)
        if not isrepoexist:
            os.mkdir(repodir)

        '''
        字符类型的时间转为时间戳
        timestr格式: 2019-06-13T06:52:36Z
        '''
        def time2Timestamp(timestr):
            timestr = timestr[0:10] + ' ' + timestr[11:-1]
            timeArray = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
            timestamp = int(time.mktime(timeArray))
            return timestamp


        csv.field_size_limit(500 * 1024 * 1024)
        bugs_dict = {}
        with open(csvfile, 'r', errors='ignore') as csv_f:
            readers = csv.DictReader(csv_f)
            for row in readers:
                del row['Title_Description']
                del row['Label_adders']
                del row['Label_removers']
                del row['Assigns']
                del row['Unassigns']
                del row['Closer']
                IssueNum = row['IssueNum']
                bugs_dict[int(IssueNum)] = row
            csv_f.close()
        bugs_dict_sorted = {}
        for i in sorted(bugs_dict):
            bugs_dict_sorted[i] = bugs_dict[i]
        del bugs_dict

        keylist = sorted(bugs_dict_sorted.keys())
        noSingle = 0
        for key in bugs_dict_sorted:
            keyDict = bugs_dict_sorted[key]
            curbug =keyDict['IssueNum']
            keybug_open_timestamp = time2Timestamp(keyDict['Created_at'])
            old_bug_list = []
            for temp in keylist:
                if temp >= key:
                    break
                old_key_dict = bugs_dict_sorted[temp]
                oldbug_closed_timestamp = time2Timestamp(old_key_dict['Closed_at'])
                if oldbug_closed_timestamp < keybug_open_timestamp:
                    old_bug_list.append(old_key_dict)
            if len(old_bug_list) > 0:
                '''如果bug文件夹不存在，则创建文件夹'''
                bugdir = repodir + '/Bug#' + curbug
                isbugexist = os.path.exists(bugdir)
                if not isbugexist:
                    os.mkdir(bugdir)

                '''#导出边到txt文档'''
                # outputfile = path + '/' + repo + '/Bug#' + keyDict['IssueNum'] + '_edge.txt'
                # getBugInput(keyDict, old_bug_list, outputfile)

                #userfile = bugdir + '/user.txt'
                #outputpath = path + '/' + repo + '/Bug#' + keyDict['IssueNum']
                #getBugInput(keyDict, old_bug_list, bugdir, userfile)
                #if report_count == 1:
                    #single += 1
                node_bug_list = []
                node_dev_list = []

                curbug = keyDict['IssueNum']
                curBugCreator = keyDict['Creator']
                curBugCreator_count = 1

                node_bug_list.append(curbug)
                edge_list = [[curbug, curBugCreator, 'report']]

                for oldBugDcit in old_bug_list:
                    oldBugNum = oldBugDcit['IssueNum']
                    node_bug_list.append(oldBugNum)
                    # 统计发布人员
                    oldBugCreator = oldBugDcit['Creator']
                    edge_list.append([oldBugNum, oldBugCreator, 'report'])
                    if oldBugCreator not in node_dev_list:
                        node_dev_list.append(oldBugCreator)
                    # 统计
                    if oldBugCreator == curBugCreator:
                        curBugCreator_count += 1

                    # 统计评论人员
                    if len(oldBugDcit['Commentators']) > 0:
                        oldBugCommentList = oldBugDcit['Commentators'][0:-1].split(';')
                        for oldBugCommentator in oldBugCommentList:
                            edge_list.append([oldBugNum, oldBugCommentator, 'comment'])
                            if oldBugCommentator not in node_dev_list:
                                node_dev_list.append(oldBugCommentator)
                            # 统计
                            if oldBugCommentator == curBugCreator:
                                curBugCreator_count += 1

                    # 统计修复人员
                    oldBugFixerList = oldBugDcit['Fixers'][0:-1].split(';')
                    for oldBugFixer in oldBugFixerList:
                        edge_list.append([oldBugNum, oldBugFixer, 'fix'])
                        if oldBugFixer not in node_dev_list:
                            node_dev_list.append(oldBugFixer)
                        # 统计
                        if oldBugFixer == curBugCreator:
                            curBugCreator_count += 1

                #print('bug#%s的发布人员出现在边中的次数为：%d' % (curbug, curBugCreator_count))
                '''写文件'''
                if len(edge_list) > 0:
                    node_developer_file = bugdir + '/node_developer.txt'
                    with open(node_developer_file, 'w', encoding='utf-8') as node_devf:
                        for developer in node_dev_list:
                            node_devf.write(developer + '\n')
                        node_devf.close()

                    node_bug_file = bugdir + '/node_bug.txt'
                    with open(node_bug_file, 'w', encoding='utf-8') as node_bugf:
                        for bug in node_bug_list:
                            node_bugf.write(bug + '\n')
                        node_bugf.close()

                    edge_file = bugdir + '/edge.txt'
                    with open(edge_file, 'w', encoding='utf-8') as edgef:
                        for sublist in edge_list:
                            outEdge = sublist[0] + ' ' + sublist[1] + ' ' + sublist[2] + '\n'
                            edgef.write(outEdge)
                        edgef.close()
                    # 获取
                    #print('得到项目%s缺陷问题%s的图数据:节点和边' % (keyDict['Repo'], curbug))
                if curBugCreator_count > 1:
                    noSingle += 1
        print('项目%s中缺陷发布人员写作开发的次数为%d,总缺陷数为%d,比例为%f' % (repo, noSingle, len(bugs_dict_sorted), noSingle / len(bugs_dict_sorted)))
        return