import json
import time
import itertools
import requests


global token_list
token_list = [
    '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',
    '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',
    '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',
    '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']
token_iter = itertools.cycle(token_list)

headers_for_requests = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Accept': 'application/vnd.github+json',
        'Authorization': 'token ' + token_iter.__next__()}


# access_token = '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'
# headers_for_requests = {
#     'Authorization': 'token ' + access_token
# }
proxy = {
    'http': None,
    'https': None
}


def crawl_Url(url: str):
    for i in range(100):
        try:
            response = requests.request('GET', url, proxies=proxy, headers=headers_for_requests)
            response_dict = json.loads(response.text)
            if 'message' in response_dict:
                if 'Not Found' in response.text:
                    print('Not Found')
                    return None
                if 'API rate limit exceeded' in response.text:
                    print('API rate limit exceeded')
                    # time.sleep(3600)
                    time.sleep(60)
                    continue
            return response.json()
        except Exception:
            continue
    return None

def request(url: str):
    for i in range(100):
        try:
            response = requests.request('GET', url, proxies=proxy, headers=headers_for_requests)
            response_dict = json.loads(response.text)
            if 'message' in response_dict:
                if 'Not Found' in response.text:
                    print('Not Found')
                    return None
                if 'API rate limit exceeded' in response.text:
                    print('API rate limit exceeded')
                    time.sleep(3600)
                    continue
            return response
        except Exception:
            continue
    return None


