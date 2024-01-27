#-*- coding : utf-8-*-
# coding:unicode_escape

import os, csv, json
# from build_graph import Build_Graph
from preprocess_text import vectorlize_string
import torch
from transformers import BertModel, BertConfig, BertTokenizer

def textFeature():
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

    # path = "F:/research_3/data"
    repo_list = ['ant-design', 'electron', 'flutter', 'kubernetes', 'next.js', 'PowerToys', 'tensorflow', 'terminal',
                 'TypeScript']
    for repo in repo_list:
        data_csvfile = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + '_RLink_top1_v2.csv'
        logdict = {}
        csv.field_size_limit(500 * 1024 * 1024)
        with open(data_csvfile, 'r', encoding='utf-8', errors='ignore') as data_csvf:#encoding='utf-8',
            readers = csv.DictReader(data_csvf)
            for row in readers:
                bug = row["IssueNum"]
                # fixlist = [fixer for fixer in row["Fixers"].split(';')]
                # bugInfodict = {"fixers": fixlist}
                text_preprocess = row["Title_Description"]
                text = vectorlize_string(text_preprocess)
                input_ids = bert_uncased_tokenizer(text, truncation=True, max_length=512)
                input_ids = torch.tensor(input_ids['input_ids']).unsqueeze(0).to(device)
                with torch.no_grad():
                    pooled_output = bert_uncased_model(input_ids)
                    pooled_output = pooled_output[1].to("cuda")
                logdict[bug] = [float(x) for x in pooled_output[0]]
                print('得到项目%s中缺陷问题%s的文本特征' % (repo, bug))
            data_csvf.close()
        outputconfig = "F:/research_3/data/zzz_csv_data/data-csv/" + repo + "/log_RLink.config"
        with open(outputconfig, 'w', encoding='utf-8') as outf:
            json.dump(logdict, outf)
            outf.close()
        print('得到项目%s的所有文本特征', repo)
    return


if __name__ == "__main__":
    textFeature()

