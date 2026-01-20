#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
损失函数实现
包含Point-wise和Pair-wise模型使用的各种损失函数
"""

import numpy as np


class BinaryCrossEntropyLoss:
    """
    二分类交叉熵损失函数
    用于Point-wise模型
    L = -y*log(y') - (1-y)*log(1-y')
    """
    
    def __init__(self):
        """初始化损失函数"""
        pass
    
    def ops(self, y_pred, y_true):
        """
        计算损失
        :param y_pred: 预测概率 [0, 1]
        :param y_true: 真实标签 (0 或 1)
        :return: 损失值
        """
        epsilon = 1e-15  # 防止log(0)
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        loss = -y_true * np.log(y_pred) - (1 - y_true) * np.log(1 - y_pred)
        return loss


class PairwiseHingeLoss:
    """
    Pair-wise 采用 hinge loss
    L = max(0, margin - (S(Q,D+) - S(Q,D-)))
    """
    
    def __init__(self, config=None):
        """
        初始化损失函数
        :param config: 配置字典，包含margin参数
        """
        if config is None:
            config = {}
        self.margin = float(config.get("margin", 1.0))
    
    def ops(self, score_pos, score_neg):
        """
        计算损失
        :param score_pos: 正样本得分 S(Q, D+)
        :param score_neg: 负样本得分 S(Q, D-)
        :return: 损失值
        """
        # 确保score_pos和score_neg是numpy数组或标量
        if isinstance(score_pos, (list, tuple)):
            score_pos = np.array(score_pos)
        if isinstance(score_neg, (list, tuple)):
            score_neg = np.array(score_neg)
        
        loss = np.maximum(0.0, self.margin - (score_pos - score_neg))
        return np.mean(loss) if hasattr(loss, 'mean') else loss


class PairwiseLogLoss:
    """
    Pair-wise 采用 log loss
    L = log(1 + exp(score_neg - score_pos))
    或使用sigmoid: L = sigmoid(score_neg - score_pos)
    """
    
    def __init__(self, config=None):
        """
        初始化损失函数
        :param config: 配置字典（可选）
        """
        pass
    
    def ops(self, score_pos, score_neg):
        """
        计算损失
        :param score_pos: 正样本得分
        :param score_neg: 负样本得分
        :return: 损失值
        """
        # 确保score_pos和score_neg是numpy数组或标量
        if isinstance(score_pos, (list, tuple)):
            score_pos = np.array(score_pos)
        if isinstance(score_neg, (list, tuple)):
            score_neg = np.array(score_neg)
        
        diff = score_neg - score_pos
        # 使用sigmoid的简化形式
        loss = 1 / (1 + np.exp(-diff))
        return np.mean(loss) if hasattr(loss, 'mean') else loss


class SoftmaxWithLoss:
    """
    Softmax损失函数
    用于多分类任务
    """
    
    def __init__(self):
        """初始化损失函数"""
        pass
    
    def ops(self, pred, label):
        """
        计算softmax交叉熵损失
        :param pred: 预测logits
        :param label: 真实标签（one-hot编码）
        :return: 损失值
        """
        # 计算softmax
        exp_pred = np.exp(pred - np.max(pred, axis=-1, keepdims=True))
        softmax_pred = exp_pred / np.sum(exp_pred, axis=-1, keepdims=True)
        
        # 计算交叉熵
        epsilon = 1e-15
        softmax_pred = np.clip(softmax_pred, epsilon, 1 - epsilon)
        loss = -np.sum(label * np.log(softmax_pred), axis=-1)
        
        return np.mean(loss)


if __name__ == '__main__':
    # 测试二分类交叉熵损失
    bce_loss = BinaryCrossEntropyLoss()
    loss1 = bce_loss.ops(0.8, 1)  # 预测0.8，真实标签1
    loss2 = bce_loss.ops(0.2, 0)  # 预测0.2，真实标签0
    print(f"二分类交叉熵损失: {loss1:.4f}, {loss2:.4f}")
    
    # 测试Hinge损失
    hinge_loss = PairwiseHingeLoss({"margin": 1.0})
    loss3 = hinge_loss.ops(0.9, 0.3)  # 正样本得分0.9，负样本得分0.3
    loss4 = hinge_loss.ops(0.5, 0.6)  # 正样本得分0.5，负样本得分0.6（应该产生损失）
    print(f"Hinge损失: {loss3:.4f}, {loss4:.4f}")
    
    # 测试Log损失
    log_loss = PairwiseLogLoss()
    loss5 = log_loss.ops(0.9, 0.3)
    loss6 = log_loss.ops(0.5, 0.6)
    print(f"Log损失: {loss5:.4f}, {loss6:.4f}")
