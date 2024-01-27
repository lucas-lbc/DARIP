import os, sys
import time
import networkx as nx
import random
import numpy as np
import math
import itertools
from collections import Counter



class MetaPathGenerator:
    """MetaPathGenerator

    Args:
        dataset     - the dataset to work on
        length      - the length of random walks to be generated
        num_walks   - the number of random walks start from each node
    """

    def __init__(self, G, length=100, coverage=10000):
        self._walk_length = length
        self._coverage = coverage
        #self._dataset = dataset
        self.G = G

        self.walks = []
        self.pairs = []

    def get_node_within_edge(self, type):
        def type_of_node(node):
            return G.nodes[node]['type']

        node_withedge_list = []
        G = self.G
        edgelist = G.edges()
        for tup in edgelist:
            for node in tup:
                if type_of_node(node) == type and node not in node_withedge_list:
                    node_withedge_list.append(node)
        return node_withedge_list

    def get_nodelist(self, type=None):
        """ Get specific type or all nodes of nodelist in the graph

        Args:
            type - The entity type of the entity.
                   If set as `None`, then all types of nodes would be returned.

        Return:
            nodelist - the list of node with `type`
        """
        G = self.G
        if not G.number_of_edges() or not G.number_of_nodes():
            sys.exit("Graph should be initialized before get_nodelist()!")

        if not type:
            return list(G.nodes)
        nodelist = []
        for node in list(G.nodes):
            nodetype = "developer"
            if node.isdigit():#纯数字
                nodetype = "user"
            #nodetype = G.nodes[node].type#['type']
            if type == nodetype:
                nodelist.append(node)
        return nodelist

    def generate_metapaths_walk(self, patterns, alpha):
        """ Generate Walk based on the metapath

        Generating random walk from the Tripartite graph
        A candidate pattern pool is:
            "D-f-B-r-D": specifies ...
            "D-C-B-r-D": specifies ...
            "D-c-B-f-D": specifies ...
            "D-c-B-c-D": specifies 2 A's answered a question proposed by a same R

        Args:
            meta_pattern - the pattern that guides the walk generation
            alpha - probability of restart

        Return:
            walks - a set of generated random walks
        """
        G = self.G
        num_walks, walk_len = self._coverage, self._walk_length
        rand = random.Random(0)

        #print("Generating Meta-paths ...")

        if not G.number_of_edges() or not G.number_of_nodes():
            sys.exit("Graph should be initialized before generate_walks()!")

        walks = []
        # addReportNewBugBehavior = False
        # if addReportNewBugBehavior:
        #     walks.append(init_walk)

        for meta_pattern in patterns:  # Generate by patterns
            #print("\tNow generating meta-paths from pattern: \"{}\" ..."
            #      .format(meta_pattern))

            #start_entity_type = meta_pattern[0]
            #start_node_list = self.get_nodelist(start_entity_type)
            #start_node_list = self.get_nodelist("developer")
            #start_node_list = self.get_node_within_edge(type="developer")
            start_node_list = self.get_nodelist(type="developer")
            for cnt in range(num_walks):  # Iterate the node set for cnt times
                #print("Count={}".format(cnt))
                rand.shuffle(start_node_list)#打乱列表顺序，换成有边的节点list
                total = len(start_node_list)
                for ind, start_node in enumerate(start_node_list):
                    #if ind % 3000 == 0:
                        #print("Finished {:.2f}".format(ind / total))

                    walkseq = self.__meta_path_walk(start=start_node, alpha=alpha, pattern=meta_pattern)
                    if " " in walkseq:
                        walks.append(walkseq)

        #print("Done!")
        self.walks = walks
        return

    def generate_random_walk(self):
        """ Generate Random Walk

        Generating random walk from the Tripartite graph
        Args:
            meta_pattern - the pattern that guides the walk generation
            alpha - probability of restart

        Return:
            walks - a set of generated random walks
        """
        G = self.G
        num_walks, walk_len = self._coverage, self._walk_length
        rand = random.Random(0)

        print("Generating Meta-paths ...")

        if not G.number_of_edges() or not G.number_of_nodes():
            sys.exit("Graph should be initialized before generate_walks()!")

        walks = []

        print("\tNow generating meta-paths from deepwalk ...")
        start_node_list = self.get_nodelist()
        for cnt in range(num_walks):  # Iterate the node set for cnt times
            print("Count={}".format(cnt))
            rand.shuffle(start_node_list)
            total = len(start_node_list)
            for ind, start_node in enumerate(start_node_list):
                if ind % 3000 == 0:
                    print("Finished {:.2f}".format(ind/total))
                walks.append(
                    self.__random_walk(start=start_node))

        print("Done!")
        self.walks = walks
        return

    def __random_walk(self, start=None):
        """Single Random Walk Generator

        Args:
            rand - an random object to generate random numbers
            start - starting node

        Return:
            walk - the single walk generated
        """
        G = self.G
        rand = random.Random()
        walk = [start]
        cur_node = start
        while len(walk) <= self._walk_length:
            possible_next_nodes = [neighbor
                                   for neighbor in G.neighbors(cur_node)]
            next_node = rand.choice(possible_next_nodes)
            walk.append(next_node)
            cur_node = next_node

        return " ".join(walk)

    def __meta_path_walk(self, start=None, alpha=0.0, pattern=None):
        """Single Walk Generator

        Generating a single random walk that follows a meta path of `pattern`

        Args:
            rand - an random object to generate random numbers
            start - starting node
            alpha - probability of restarts
            pattern - (string) the pattern according to which to generate walks
            walk_len - (int) the length of the generated walk

        Return:
            walk - the single walk generated

        """
        G = self.G

        def type_of_node(node):
            return G.nodes[node]['type']

        def type_of_edge(node1, node2):
            return G.edges[node1, node2]['type']

        rand = random.Random()
        # Checking pattern is correctly initialized
        if not pattern:
            sys.exit("Pattern is not specified when generating meta-path walk")

        node_idx = 0#1
        walk = [start]
        cur_node = start

        # Generating meta-paths
        while len(walk) <= self._walk_length or node_idx != len(pattern):

            # Updating the pattern index
            node_idx = node_idx if node_idx != len(pattern)-1 else 0

            # Decide whether to restart
            if rand.random() >= alpha:
                # Find all possible next neighbors
                possible_next_node = []
                for neighbor in G.neighbors(cur_node):
                    type = type_of_node(neighbor)[0]
                    nb_type = pattern[node_idx+2].lower()
                    if type_of_node(neighbor)[0] == pattern[node_idx+2].lower():
                        edge_type = pattern[node_idx+1]#没有+1
                        et = type_of_edge(neighbor, cur_node)[0]
                        if edge_type == type_of_edge(neighbor, cur_node)[0]:
                            possible_next_node.append(neighbor)
                '''
                possible_next_node = [neighbor
                                      for neighbor in G.neighbors(cur_node)
                                      if (type_of_node(neighbor)[0] == pattern[node_idx].lower()) and (type_of_edge(neighbor, cur_node)[0]) == edge_type]
                '''
                # Random choose next node
                if len(possible_next_node) > 0:
                    next_node = rand.choice(possible_next_node)
                else:
                    break
            else:
                next_node = walk[0]

            walk.append(next_node)
            cur_node = next_node
            node_idx += 2
            if len(walk) == self._walk_length:
                break
        return " ".join(walk)

    def write_metapaths(self, OUTPUT):
        """Write Metapaths to files

        Args:
            walks - The walks generated by `generate_walks`
        """

        #print("Writing Generated Meta-paths to files ...", end=" ")

        '''
        DATA_DIR = os.getcwd() + "\metapath"
        OUTPUT = DATA_DIR + str(self._coverage) + "_" + str(self._walk_length) + ".txt"
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        '''
        #DATA_DIR = "F:/research_3/data/zzz_csv_data/data-csv/ant-design/Bug#39841"
        #OUTPUT = DATA_DIR + '/' + str(self._coverage) + "_" + str(self._walk_length) + ".txt"
        with open(OUTPUT, "w") as fout:
            for walk in self.walks:
                print("{}".format(walk), file=fout)

        #print("Done!")

    def path_to_pairs(self, window_size):
        """Convert all metapaths to pairs of nodes

        Args:
            walks - all the walks to be translated
            window_size - the sliding window size
        Return:
            pairs - the *shuffled* pair corpus of the dataset
        """
        pairs = []
        if not self.walks:
            sys.exit("Walks haven't been created.")
        for walk in self.walks:
            walk = walk.strip().split(' ')
            for pos, token in enumerate(walk):
                lcontext, rcontext = [], []
                lcontext = walk[pos - window_size: pos] \
                    if pos - window_size >= 0 \
                    else walk[:pos]

                if pos + 1 < len(walk):
                    rcontext = walk[pos + 1: pos + window_size] \
                        if pos + window_size < len(walk) \
                        else walk[pos + 1:]

                context_pairs = [[token, context]
                                 for context in lcontext + rcontext]
                pairs += context_pairs
        np.random.shuffle(pairs)
        self.pairs = pairs
        return

    def write_pairs(self, OUTPUT):
        """Write all pairs to files
        Args:
            pairs - the corpus
        Return:
        """
        print("Writing Generated Pairs to files ...")
        '''
        DATA_DIR = os.getcwd() + "/corpus/"
        OUTPUT = DATA_DIR + self._dataset + "_" + \
                 str(self._coverage) + "_" + str(self._walk_length) + ".txt"
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        '''
        #DATA_DIR = "F:/research_3/data/zzz_csv_data/data-csv/ant-design/Bug#39841"
        #OUTPUT = DATA_DIR + '/corpus_' + str(self._coverage) + "_" + str(self._walk_length) + ".txt"
        with open(OUTPUT, "w") as fout:
            for pair in self.pairs:
                print("{} {}".format(pair[0], pair[1]), file=fout)
        return

    def down_sample(self):
        """Down sampling the training sets

        1. Remove all the duplicate tuples such as "A_11 A_11"
        2. Take log of all tuples as a down sampling
        """

        pairs = self.pairs
        pairs = [(pair[0], pair[1])
                 for pair in pairs
                 if pair[0] != pair[1]]
        cnt = Counter(pairs)
        down_cnt = [[pair] * math.ceil(math.log(count))
                    for pair, count in cnt.items()]
        self.pairs = list(itertools.chain(*down_cnt))
        np.random.shuffle(self.pairs)

def getGraphForBug(bugdir):

    edgefile = bugdir + '/edge.txt'
    node_bugfile = bugdir + '/node_bug.txt'
    node_userfile = bugdir + '/node_developer.txt'

    buglist = []
    with open(node_bugfile, 'r', encoding='utf-8') as bugf:
        for line in bugf.readlines():
            line = line.rstrip()
            buglist.append(line)
        bugf.close()

    userlist = []
    with open(node_userfile, 'r', encoding='utf-8') as userf:
        for line in userf.readlines():
            line = line.rstrip()
            userlist.append(line)
        userf.close()

    edgelist = []
    with open(edgefile, 'r', encoding='utf-8') as edgef:
        for line in edgef.readlines():
            line_list = line.rstrip().split(' ')
            edgelist.append(line_list)
        edgef.close()

    '''图的定义'''
    G = nx.Graph()
    G.add_nodes_from(buglist, type='bug')
    G.add_nodes_from(userlist, type='developer')

    for edgeinfo in edgelist:
        #if edgeinfo[2] == "create":
        #    edgeinfo[2] = "report"
        tup = ([edgeinfo[0], edgeinfo[1]])
        G.add_edges_from([tup], type=edgeinfo[2])
        #nx.draw_networkx_edges(g, pos=nx.circular_layout(g), edgelist=[tup], label=edgeinfo[2])
    # nx.draw_networkx_nodes(g, pos=nx.circular_layout(g), nodelist=buglist, node_color='red', label='bug')
    # nx.draw_networkx_nodes(g, pos=nx.circular_layout(g), nodelist=buglist, node_color='green', label='user')
    '''图的显示'''
    #print(G.number_of_nodes())#查看点的数量
    #print(G.nodes())#查看所有点的信息（list）
    #print(G.number_of_edges())#查看边的数量
    #print(G.edges())#查看所有边的信息（list中的每个元素时一个tuple）
    #print(nx.get_node_attributes(g, 'type'))
    #print(nx.get_edge_attributes(g, 'type'))
    #nx.draw(g)
    #print(G.nodes['afc163'])
    #kn = G.neighbors('afc163')
    #print(kn)
    return G

'''
if __name__ == "__main__":
    ticks_1 = time.time()
    print ("当前时间戳为:", ticks_1)
    bugdir = "F:/research_3/data/zzz_csv_data/data-csv/ant-design" + "/Bug#39841"
    #构建异构图
    G = getGraphForBug(bugdir)
    gw = MetaPathGenerator(length=13, coverage=20, G=G)
    gw.generate_metapaths_walk(patterns=["DfBrD", "DcBrD", "DcBfD", "DcBcD"], alpha=0)
    gw.path_to_pairs(window_size=4)
    gw.down_sample()
    gw.write_metapaths()
    gw.write_pairs()
    ticks_2 = time.time()
    print("当前时间戳为:", ticks_2)
    print("时间间隔为： ", ticks_2-ticks_1)
'''