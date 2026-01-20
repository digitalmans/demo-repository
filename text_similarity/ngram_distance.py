#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
N-gram 距离计算
"""


class NGram:
    """
    计算 N-gram 的类
    """
    
    def __init__(self, n=2):
        """
        设置参数n, 默认为2
        :param n: N-gram的N值
        """
        self.n = n
    
    def distance(self, s0, s1):
        """
        计算输入文本的N-gram距离
        :param s0: 字符串1
        :param s1: 字符串2
        :return: N-gram距离
        """
        if s0 is None:
            raise TypeError("Argument s0 is NoneType.")
        if s1 is None:
            raise TypeError("Argument s1 is NoneType.")
        
        # 如果两个字符串相同，距离为0
        if s0 == s1:
            return 0.0
        
        special = '\n'
        sl = len(s0)
        tl = len(s1)
        
        # 如果任一字符串为空，返回1.0
        if sl == 0 or tl == 0:
            return 1.0
        
        cost = 0
        # 如果字符串长度小于n，使用简单的字符匹配
        if sl < self.n or tl < self.n:
            for i in range(min(sl, tl)):
                if s0[i] == s1[i]:
                    cost += 1
            return 1.0 - (cost / max(sl, tl))
        
        # 创建sa数组，用特殊字符填充
        sa = [''] * (sl + self.n - 1)
        for i in range(len(sa)):
            if i < self.n - 1:
                sa[i] = special
            else:
                sa[i] = s0[i - self.n + 1]
        
        # 初始化DP数组
        p = [0.0] * (sl + 1)
        d = [0.0] * (sl + 1)
        t_j = [''] * self.n
        
        # 初始化p数组
        for i in range(sl + 1):
            p[i] = 1.0 * i
        
        # 计算距离
        for j in range(1, tl + 1):
            if j < self.n:
                for ti in range(self.n):
                    if ti < self.n - j:
                        t_j[ti] = special
                    else:
                        t_j[ti] = s1[ti - (self.n - j)]
            else:
                t_j = list(s1[j - self.n:j])
            
            d[0] = 1.0 * j
            
            for i in range(1, sl + 1):
                cost = 0
                tn = self.n
                for ni in range(self.n):
                    if sa[i - 1 + ni] != t_j[ni]:
                        cost += 1
                    elif sa[i - 1 + ni] == special:
                        tn -= 1
                
                ec = cost / tn if tn > 0 else 1.0
                d[i] = min(d[i - 1] + 1, p[i] + 1, p[i - 1] + ec)
            
            p, d = d, p
        
        return p[sl] / max(tl, sl)


if __name__ == '__main__':
    twogram = NGram(2)
    print(twogram.distance('ABCD', 'ABTUIO'))
    
    s1 = 'Adobe CreativeSuite 5 Master Collection from cheap 4zp'
    s2 = 'Adobe CreativeSuite 5 Master Collection from cheap dlx'
    fourgram = NGram(4)
    print(fourgram.distance(s1, s2))
