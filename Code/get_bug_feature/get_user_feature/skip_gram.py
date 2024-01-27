from gensim.models import Word2Vec

class SkipGram:
    def __init__(self, config):
        vector_size = config["vector_size"]
        window = config["window_size"]
        negative = config["negative"]
        alpha = config["alpha"]
        min_alpha = config["min_alpha"]
        self.model = Word2Vec(vector_size=vector_size,  # Embedding维数 256
                          window=window,  # 窗口宽度 4
                          workers=4,
                          sg=1,  # Skip-Gram模型
                          hs=0,  # 不加分层softmax
                          negative=negative,  # 负采样 3
                          alpha=alpha,  # 初始学习率 0.03
                          min_alpha=min_alpha,  # 最小学习率 0.0007
                          seed=14  # 随机数种子
                          )


    def obtain_walks(self, walkfile):
        walks = []
        with open(walkfile, 'r', encoding='utf-8') as walkf:
            for line in walkf.readlines():
                linelist = line.rstrip().split(' ')
                walks.append(linelist)
            walkf.close()
        self.walks = walks
        return walks


    def skip_gram(self, walks):
        model = self.model
        # 用随机游走序列构建词汇表
        model.build_vocab(walks, progress_per=2)
        # 训练
        model.train(walks, total_examples=model.corpus_count, epochs=50, report_delay=1)

        # 查看某个节点的Embedding
        # print(model.wv.get_vector('afc163'))
        return


    def get_node_embedding(self, node):
        vector_size = self.model.vector_size
        vec = [0.00] * vector_size
        model = self.model
        if node in model.wv.key_to_index:
            vec = model.wv[node].tolist()
        return vec