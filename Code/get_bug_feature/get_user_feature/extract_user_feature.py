import json
import time
import os, csv
import networkx as nx
from build_graph import Build_Graph
from generate_walk import MetaPathGenerator
from generate_walk import getGraphForBug
from skip_gram import SkipGram

config = {
    "vector_size": 768,
    "window_size": 6,
    "negative": 3,
    "alpha": 0.03,
    "min_alpha": 0.0007,
    "seed": 14,
    "coverage": 10,#20
    "length": 9,#13
    "patterns": ["DfBrD", "DcBrD", "DcBfD", "DcBcD"]
}


def obtain_repo_users(repoInfoCsv):
    print('读取文件：', repoInfoCsv)
    csv.field_size_limit(500 * 1024 * 1024)
    user_list = []
    with open(repoInfoCsv, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            '''收集Fixers'''
            my_fixerslist = row['Fixers'].split(';')
            for fix in my_fixerslist:
                if fix not in user_list:
                    user_list.append(fix)
            '''收集Commentators'''
            comments_str = row['Commentators']
            if len(comments_str) > 0:
                my_commentlist = comments_str.split(';')
                for comment in my_commentlist:
                    if comment not in user_list:
                        user_list.append(comment)
            '''收集Creator'''
            creator = row['Creator']
            if creator not in user_list:
                user_list.append(creator)
        csv_f.close()
    return user_list


def calNodeVec(user, userlist):
    '''
    userlist.sort()
    vec_len = len(userlist)
    vec = [0 for i in range(vec_len)]
    index = userlist.index(user)
    vec[index] = 1
    '''
    vec = [0 for i in range(768)]
    vec[0] = 1
    return vec

'''寻找历史缺陷'''
def findOldBugs_24h(csvfile):
    currepo = ""
    csv.field_size_limit(500 * 1024 * 1024)
    traversal_bug = []
    bug_previous_bugDict = {}
    bug_user_24h_dict = {}
    bug_user_all_dict = {}
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            #收集历史缺陷
            currepo = row["Repo"]
            curbug = row['IssueNum']
            curbug_created_at_timestamp = time2Timestamp(row["Created_at"])
            curbug_closed_at_timestamp = time2Timestamp(row["Closed_at"])
            curbug_previous_buglist = []
            for tempbuglist in traversal_bug:
                traversal_bug_closed_at_timestamp = tempbuglist[2]
                if curbug_created_at_timestamp > traversal_bug_closed_at_timestamp:
                    curbug_previous_buglist.append(tempbuglist[0])
            traversal_bug.append([curbug, curbug_created_at_timestamp, curbug_closed_at_timestamp])
            bug_previous_bugDict[curbug] = curbug_previous_buglist

            #收集开发人员
            user_24h_list = []
            user_all_list = []
            '''收集Creator'''
            creator = row["Creator"]
            user_24h_list.append(creator)
            user_all_list.append(creator)
            '''收集Fixers'''
            my_fixerslist = row['Fixers'].split(';')
            for fix in my_fixerslist:
                if fix not in user_all_list:
                    user_all_list.append(fix)
            '''收集Commentators'''
            comments_str = row['Commentators']
            if len(comments_str) > 0:
                my_commentlist = comments_str.split(';')
                for comment in my_commentlist:
                    if comment not in user_all_list:
                        user_all_list.append(comment)
            '''收集Commentators_24h'''
            comments_24h_str = row['Commentators_24h']
            if len(comments_24h_str) > 0:
                my_comment_24hlist = comments_24h_str.split(';')
                for comment_24h in my_comment_24hlist:
                    if comment_24h not in user_24h_list:
                        user_24h_list.append(comment_24h)
            bug_user_24h_dict[curbug] = user_24h_list
            bug_user_all_dict[curbug] = user_all_list
        csv_f.close()

    outputstr = ""
    cooper_num = 0
    #cooper_freq = 0
    all_num = 0
    for bugnum in bug_user_24h_dict:
        is_cooper = False
        temp_user_24h_list = bug_user_24h_dict[bugnum]
        temp_old_bugs_list = bug_previous_bugDict[bugnum]
        temp_old_user_list = []
        for temp_old_bug in temp_old_bugs_list:
            temp_old_all_user_list = bug_user_all_dict[temp_old_bug]
            for temp_old_all_user in temp_old_all_user_list:
                if temp_old_all_user not in temp_old_user_list:
                    temp_old_user_list.append(temp_old_all_user)
        for temp_user_24h in temp_user_24h_list:
            if temp_user_24h in temp_old_user_list:
                is_cooper = True
        if is_cooper:
            cooper_num += 1
            outputstr += bugnum + ';'
        all_num += 1

    print('项目%s中:缺陷总数量为%d, 24h以内的贡献用户参与历史缺陷协作的数量为%s, 比例为%f' % (currepo, all_num, cooper_num, (cooper_num/all_num)))
    outputstr = outputstr[0:-1]
    return outputstr

'''寻找历史缺陷'''
def findOldBugs(csvfile):
    currepo = ""
    csv.field_size_limit(500 * 1024 * 1024)
    traversal_bug = []
    bug_previous_bugDict = {}
    bug_user_dict = {}
    bug_user_all_dict = {}
    with open(csvfile, 'r', errors='ignore') as csv_f:
        readers = csv.DictReader(csv_f)
        for row in readers:
            #收集历史缺陷
            currepo = row["Repo"]
            curbug = row['IssueNum']
            curbug_created_at_timestamp = time2Timestamp(row["Created_at"])
            curbug_closed_at_timestamp = time2Timestamp(row["Closed_at"])
            curbug_previous_buglist = []
            for tempbuglist in traversal_bug:
                traversal_bug_closed_at_timestamp = tempbuglist[2]
                if curbug_created_at_timestamp > traversal_bug_closed_at_timestamp:
                    curbug_previous_buglist.append(tempbuglist[0])
            traversal_bug.append([curbug, curbug_created_at_timestamp, curbug_closed_at_timestamp])
            bug_previous_bugDict[curbug] = curbug_previous_buglist

            #收集开发人员
            user_all_list = []
            '''收集Creator'''
            creator = row["Creator"]
            #user_list.append(creator)
            user_all_list.append(creator)
            '''收集Fixers'''
            my_fixerslist = row['Fixers'].split(';')
            for fix in my_fixerslist:
                if fix not in user_all_list:
                    user_all_list.append(fix)
            '''收集Commentators'''
            comments_str = row['Commentators']
            if len(comments_str) > 0:
                my_commentlist = comments_str.split(';')
                for comment in my_commentlist:
                    if comment not in user_all_list:
                        user_all_list.append(comment)
            # '''收集Commentators_24h'''
            # comments_24h_str = row['Commentators_24h']
            # if len(comments_24h_str) > 0:
            #     my_comment_24hlist = comments_24h_str.split(';')
            #     for comment_24h in my_comment_24hlist:
            #         if comment_24h not in user_24h_list:
            #             user_24h_list.append(comment_24h)
            bug_user_dict[curbug] = creator
            bug_user_all_dict[curbug] = user_all_list
        csv_f.close()

    outputstr = ""
    cooper_num = 0
    all_num = 0
    for bugnum in bug_user_dict:
        is_cooper = False
        reporter = bug_user_dict[bugnum]
        temp_old_bugs_list = bug_previous_bugDict[bugnum]

        for temp_old_bug in temp_old_bugs_list:
            temp_old_all_user_list = bug_user_all_dict[temp_old_bug]
            if reporter in temp_old_all_user_list:
                is_cooper = True
        if is_cooper:
            cooper_num += 1
            outputstr += bugnum + ';'
        all_num += 1

    print('项目%s中:缺陷总数量为%d, 发布人员参与历史缺陷协作的数量为%s, 比例为%f' % (currepo, all_num, cooper_num, (cooper_num/all_num)))
    outputstr = outputstr[0:-1]
    return outputstr

def time2Timestamp(timestr):
    timestr = timestr[0:10] + ' ' + timestr[11:-1]
    timeArray = time.strptime(timestr, "%Y-%m-%d %H:%M:%S")
    timestamp = int(time.mktime(timeArray))
    return timestamp

def getCooperBugs(txtfile):
    with open(txtfile, 'r') as txtf:
        oldbugstr = txtf.readlines()
        buglist = oldbugstr[0].split(";")
        txtf.close()
    return buglist

if __name__ == "__main__":
    '''
    path = "F:/research_3/data"
    repo_list = ['ant-design', 'electron', 'flutter', 'kubernetes', 'next.js', 'PowerToys', 'tensorflow', 'terminal',
                 'TypeScript', 'vscode']
    for repo in repo_list:
        user_list = []
        bug_user_dict = {}
        csvfile = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "_comment24h_textpreprocess.csv"
        cooperstr = findOldBugs(csvfile)
        outputfile = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/cooper_bugs.txt"
        with open(outputfile, 'w', encoding='utf-8') as txtf:
            txtf.write(cooperstr)
            txtf.close()
    '''
    path = "F:/research_3/data"
    repo_list = [
        # 'ant-design',
        # 'electron',
        # 'flutter',
        # 'next.js',
        # 'PowerToys',
        # 'terminal',
        'kubernetes',
        'TypeScript'
        # 'tensorflow'
        # 'vscode'
    ]
    for repo in repo_list:
        user_list = []
        #bug_user_dict = {}
        cooperbugfile = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/cooper_bugs.txt"
        cooperbuglist = getCooperBugs(cooperbugfile)
        csvfile = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + ".csv"#_comment24h_textpreprocess
        csv.field_size_limit(500 * 1024 * 1024)
        bug_report_dict = {}
        with open(csvfile, 'r', errors='ignore') as csv_f:
            readers = csv.DictReader(csv_f)
            for row in readers:
                bugs = row['IssueNum']
                if bugs not in cooperbuglist:
                    continue
                creator = row["Creator"]
                bug_report_dict[bugs] = creator
                # buginfolist = [creator]

                # #收集Fixers
                # my_fixerslist = row['Fixers'].split(';')
                # for fix in my_fixerslist:
                #     if fix not in user_list:
                #         user_list.append(fix)
                # #收集Commentators
                # comments_str = row['Commentators']
                # if len(comments_str) > 0:
                #     my_commentlist = comments_str.split(';')
                #     for comment in my_commentlist:
                #         if comment not in user_list:
                #             user_list.append(comment)
                # #收集Creator
                # #creator = row['Creator']
                # if creator not in user_list:
                #     user_list.append(creator)
            csv_f.close()

        #bug_user_config = {"Vec_Max_Length": len(user_list)}
        #config["vector_size"] = len(user_list)

        oldbugnum = []
        userConfig = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/userFeature_w6.config"
        if os.path.exists(userConfig):
            with open(userConfig, 'r', encoding='utf-8') as configf:
                config_log = json.load(configf)
                configf.close()
            for key in config_log:
                oldbugnum.append(key)
        else:
            with open(userConfig, 'w') as f:
                json.dump({}, f)

        repodir = "F:/research_3/data/zzz_csv_data/data-csv/" + repo


        for bugnum in cooperbuglist:
            if bugnum in oldbugnum:
                print('已得到项目%s中缺陷问题%s的所有人员特征, time:%s' % (
                repo, bugnum, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
                continue
            bugCreator = bug_report_dict[bugnum]
            # bugInfolist = bug_user_dict[bugnum]
            # bugCreator = bugInfolist[0]
            # bugCommentators = []
            # if len(bugInfolist) > 1:
            #     bugCommentators = bugInfolist[1]

            #随机游走的参数设置
            patterns = config["patterns"]
            coverage = config["coverage"]
            length = config["length"]

            # 提取人员特征
            SK = SkipGram(config)
            walks = []

            outwalkfile = repodir + '/Bug#' + bugnum + '/metapath_walk_w6_' + str(coverage) + '_' + str(length) + '.txt'
            isFileExist = os.path.exists(outwalkfile)
            if not isFileExist:
                #生成图
                bugfullpath = repodir + '/Bug#' + bugnum
                G = getGraphForBug(bugfullpath)
                #基于元路径生成随机游走
                gw = MetaPathGenerator(length=length, coverage=coverage, G=G)
                gw.generate_metapaths_walk(patterns=patterns, alpha=0)
                # gw.generate_random_walk()
                gw.path_to_pairs(window_size=5)#4
                gw.down_sample()
                outwalkfile = repodir + '/Bug#' + bugnum + '/metapath_walk_w6_' + str(coverage) + '_' + str(length) + '.txt'
                gw.write_metapaths(outwalkfile)

                inputwalks = gw.walks
                for linestr in inputwalks:
                    linelist = linestr.split(" ")
                    walks.append(linelist)
                #outwalkfile_corpus = repodir + '/' + bugdir + '/metapath_walk_corpus_' + str(coverage) + '_' + str(length) + '.txt'
                #gw.write_pairs(outwalkfile_corpus)
            else:
                walks = SK.obtain_walks(outwalkfile)

            SK.skip_gram(walks)

            # num_dict = {}
            #developer_vec = []
            bugCreatorVec = SK.get_node_embedding(bugCreator)
            # if len(bugCreatorVec) == 0:
            #     vector_size
            #     num_dict[bugCreator] = bugCreatorVec
            # for bugCommentator in bugCommentators:
            #     bugCmtVec = SK.get_node_embedding(bugCommentator)
            #     if len(bugCmtVec) > 0:
            #         num_dict[bugCommentator] = bugCmtVec
            # if len(num_dict) == 0:
            #     print('人员特征缺失，来源：项目%s中缺陷问题%s, time:%s' % (
            #     repo, bugnum, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            #     continue

            #bug_user_config[bugnum] = num_dict
            print('得到项目%s中缺陷问题%s的所有人员特征, time:%s' % (repo, bugnum, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

            userConfig = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/userFeature_w6.config"
            with open(userConfig, 'r', encoding='utf-8') as configf:
                old_config_log = json.load(configf)
                configf.close()

            old_config_log[bugnum] = bugCreatorVec
            with open(userConfig, 'w', encoding='utf-8') as outf:
                json.dump(old_config_log, outf)
                outf.close()


