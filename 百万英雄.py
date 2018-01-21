import os

from aip import AipOcr
from skimage.io import imread, imsave
from lxml import html
import requests

from urllib.parse import quote
from functools import lru_cache

import numpy as np
import time


client = AipOcr('10707615', 'SD7mlLIDPYNqmsj8KeS2F5Xd', 'QWFeiCoNvTQCDpTtGVGzgbItttV5a77W ')


def screenshoot():
    """
    屏幕截图

    todo 将图片保存起来，方便以后调试
    todo 寻找其它更快速的截图方式
    todo 先降低屏幕分辨率再截图可能加快速度
    """
    os.system('adb shell screencap -p /sdcard/1.png')
    os.system('adb pull /sdcard/1.png ./')


def crop():
    """
    裁剪图片
    将屏幕截图裁剪成问题和候选项答案的图片并保存。
    默认输入图片是1.png，输出图片是Q.png,A1.png,A2.png,A3.png
    返回值True表示成功分割，false表示分割失败

    todo: 处理答案的背景，去除灰色背景
    """
    img = imread('1.png', as_grey=True)
    img=img[:, 80:-80]


    l = img.sum(-1)

    t = (l==img.shape[1])

    # 判断是否有问题出现在屏幕上
    if np.ones([t.shape[0]])[t].sum() < 100:
        return False

    spans = []
    last = False

    for idx, e in enumerate(t):
        if e != last:
            if e == 1:
                spans.append(idx)
            else:
                spans[-1] = (spans[-1], idx+1)
        last = e

    # print(spans)

    print(f'问题有{len(spans)-5}行')

    Q = img[spans[0][1]:spans[-4][0]]
    imsave('Q.png', Q)
    A1 = img[spans[-4][1]:spans[-3][0]]
    imsave('A1.png', A1)
    A2 = img[spans[-3][1]:spans[-2][0]]
    imsave('A2.png', A2)
    A3 = img[spans[-2][1]:spans[-1][0]]
    imsave('A3.png', A3)
    return True


def parseQA():
    """
    分析图片
    todo 添加重试机制
    """
    Q = ''.join([k['words'] for k in client.basicGeneral(open('Q.png','rb').read())['words_result']])
    Q = Q.split('.', 1)[1]
    A1 = ''.join([k['words'] for k in client.basicGeneral(open('A1.png','rb').read())['words_result']])
    A2 = ''.join([k['words'] for k in client.basicGeneral(open('A2.png','rb').read())['words_result']])
    A3 = ''.join([k['words'] for k in client.basicGeneral(open('A3.png','rb').read())['words_result']])
    return Q, A1, A2, A3


@lru_cache()
def search(q):
    r = requests.get('http://www.baidu.com/s?wd='+quote(q))
    tree = html.document_fromstring(r.content)
        
    num = int(''.join(tree.xpath("//div[@class='search_tool']")[0].tail[11:-1].split(',')))
    return num


def findBestPMI(Q, A1, A2, A3):
    def f1(A):
        res = search(Q+' '+A)
        print(A, res)
        return res
    def f2(A):
        res = search(Q+' '+A) / search(A)
        print(A, res)
        return res
    ans1 = max(A1, A2, A3, key=f1)
    ans2 = max(A1, A2, A3, key=f2)
    if ans1==ans2:
        return ans1
    return 


def findBestQA(Q, A1, A2, A3):
    r = requests.get('http://www.baidu.com/s?wd='+quote(Q))
    tree = html.document_fromstring(r.content)

    exactqa = tree.xpath("//div[@class='op_exactqa_s_answer']")
    if exactqa:
        qa = exactqa[0]
        text = qa.text_content().strip()
        print("知识图谱答案是:")
        print(text)
        print('-'*10)

        if text == A1 or A1 in text or text in A1:
            return 0
        if text == A2 or A2 in text or text in A2:
            return 1
        if text == A3 or A3 in text or text in A3:
            return 2
        # 以后使用相似度
        # https://console.bce.baidu.com/ai/?_=1516460156286#/ai/nlp/overview/index

    
def findBestAnswer(Q, A1, A2, A3):
    a = findBestQA(Q, A1, A2, A3)
    if a is not None:
        return a
    a = findBestPMI(Q, A1, A2, A3)
    if a is not None:
        return a


def test():
    findBestAnswer("世界上最大湖是什么?", "里海", "洞庭湖", "鄱阳湖")
    findBestAnswer("美国特区华盛顿使用的是哪个时区的时间?", "东四区", "西五区", "鄱阳湖")


def main():
    q = True
    while True:
        screenshoot()
        if crop() and q:
            Q, A1, A2, A3 = parseQA()
            r = findBestAnswer(Q, A1, A2, A3)
            print("最后的答案是:", r)
            print()
            time.sleep(10)
            q = False  # 给出答案时不识别
        

if __name__ == '__main__':
    main()
