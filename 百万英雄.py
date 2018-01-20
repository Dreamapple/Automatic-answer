import os
from PIL import Image

from aip import AipOcr
from skimage.io import imread, imsave

client = AipOcr('10707615', 'SD7mlLIDPYNqmsj8KeS2F5Xd', 'QWFeiCoNvTQCDpTtGVGzgbItttV5a77W ')

qq=open('Q.png', 'rb')

def screenshoot(idx=0):
    os.system(f'adb shell screencap -p /sdcard/1.png')
    os.system(f'adb pull /sdcard/1.png ./')


def crop():
    img = imread('1.png', True)

    gg=img[:, 80:-80]


    l = gg.sum(-1)

    t = (l==gg.shape[1])

    spans = []
    last = False

    for idx, e in enumerate(t):
        if e != last:
            if e == 1:
                spans.append(idx)
            else:
                spans[-1] = (spans[-1], idx+1)
        last = e

    print(spans)

    if len(spans)==6:
        print('问题只有一行')
    else:
        print(f'问题有{len(spans)-5}行')

    Q = gg[spans[0][1]:spans[-4][0]]
    imsave('Q.png', Q)
    A1 = gg[spans[-4][1]:spans[-3][0]]
    imsave('A1.png', A1)
    A2 = gg[spans[-3][1]:spans[-2][0]]
    imsave('A2.png', A2)
    A3 = gg[spans[-2][1]:spans[-1][0]]
    imsave('A3.png', A3)


def parseQA():
    Q = ''.join([k['words'] for k in client.basicGeneral(open('Q.png','rb').read())['words_result']])
    Q = Q.split('.', 1)[1]
    A1 = ''.join([k['words'] for k in client.basicGeneral(open('A1.png','rb').read())['words_result']])
    A2 = ''.join([k['words'] for k in client.basicGeneral(open('A2.png','rb').read())['words_result']])
    A3 = ''.join([k['words'] for k in client.basicGeneral(open('A3.png','rb').read())['words_result']])
    return Q, A1, A2, A3

from urllib.parse import quote
from functools import lru_cache

@lru_cache()
def search(q):
    r = requests.get('http://www.baidu.com/s?wd='+quote(q))
    tree = html.document_fromstring(r.content)
        
    num = int(''.join(tree.xpath("//div[@class='search_tool']")[0].tail[11:-1].split(',')))
    return num


def findBestPMI(Q, A1, A2, A3):
    def f(A):
        res = search(Q+' '+A) #/ (search(Q) * search(A))
        print(A, res)
        return res
    A = max(A1, A2, A3, key=f)
    return A


def findBestQA(Q, A1, A2, A3):
    r = requests.get('http://www.baidu.com/s?wd='+quote(Q))
    tree = html.document_fromstring(r.content)

    exactqa = tree.xpath("//div[@class='op_exactqa_s_answer']")
    if exactqa:
        qa = exactqa[0]
        text = qa.text_content().strip()
        print("知识图谱答案是", text)

        if text == A1:
            return 0
        if text == A2:
            return 1
        if text == A3:
            return 2
        # 以后使用相似度
        # https://console.bce.baidu.com/ai/?_=1516460156286#/ai/nlp/overview/index


from lxml import html
import requests



    
def main():
    screenshoot()
    crop()
    Q, A1, A2, A3 = parseQA()
    r = findBest(Q, A1, A2, A3)
    print(r)
