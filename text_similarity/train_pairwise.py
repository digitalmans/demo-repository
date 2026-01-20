#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
训练Pair-wise模型
代码3.7 训练网络模型
"""

import json
import logging
import sys
import os
from .pairwise import PairwiseModel
from .loss_functions import PairwiseHingeLoss, PairwiseLogLoss, BinaryCrossEntropyLoss


def load_config(config_file):
    """
    导入配置文件数据
    :param config_file: 配置文件路径
    :return: 配置字典
    """
    try:
        with open(config_file, "r", encoding='utf-8') as f:
            conf = json.load(f)
    except Exception as e:
        logging.error(f"load json file is error: {config_file}, {e}")
        return {}
    
    conf_dict = {}
    for k in conf:
        conf_dict.update(conf[k])
    
    logging.debug("\n".join([f"{u}={conf_dict[u]}" for u in conf_dict]))
    return conf_dict


def train(conf_dict):
    """
    训练网络
    :param conf_dict: 配置字典
    """
    training_mode = conf_dict.get("training_mode", "pairwise")
    
    # 创建模型
    model = PairwiseModel(
        representation_method=conf_dict.get("representation_method", "bow"),
        matching_method=conf_dict.get("matching_method", "cosine"),
        embedding_dim=int(conf_dict.get("embedding_dim", 100)),
        vocab_size=int(conf_dict.get("vocab_size", 10000)),
        margin=float(conf_dict.get("margin", 1.0))
    )
    
    # 采用 point-wise 模型
    if training_mode == "pointwise":
        from .pointwise import PointWiseModel
        model = PointWiseModel(
            representation_method=conf_dict.get("representation_method", "bow"),
            matching_method=conf_dict.get("matching_method", "cosine"),
            embedding_dim=int(conf_dict.get("embedding_dim", 100)),
            vocab_size=int(conf_dict.get("vocab_size", 10000))
        )
        
        # 设置loss函数
        loss_layer = BinaryCrossEntropyLoss()
        print("使用Point-wise模型和BinaryCrossEntropyLoss")
        
    # 采用 pair-wise 模型
    elif training_mode == "pairwise":
        # 设置loss函数
        loss_type = conf_dict.get("loss_type", "hinge")
        if loss_type == "hinge":
            loss_layer = PairwiseHingeLoss(conf_dict)
        elif loss_type == "log":
            loss_layer = PairwiseLogLoss(conf_dict)
        else:
            raise ValueError(f"Unsupported loss type: {loss_type}")
        
        print(f"使用Pair-wise模型和{loss_type}损失函数")
        
    else:
        print(f"training mode not supported: {training_mode}", file=sys.stderr)
        sys.exit(1)
    
    # 定义优化器（简化版，实际应使用Adam等）
    learning_rate = float(conf_dict.get("learning_rate", 0.001))
    print(f"学习率: {learning_rate}")
    print("开始训练...")
    
    # 这里应该加载训练数据并执行训练循环
    # 由于没有实际的数据加载器，这里只是示例框架
    print("训练框架已设置完成")


def predict(conf_dict):
    """
    预测
    :param conf_dict: 配置字典
    """
    training_mode = conf_dict.get("training_mode", "pairwise")
    
    if training_mode == "pairwise":
        model = PairwiseModel(
            representation_method=conf_dict.get("representation_method", "bow"),
            matching_method=conf_dict.get("matching_method", "cosine"),
            embedding_dim=int(conf_dict.get("embedding_dim", 100)),
            vocab_size=int(conf_dict.get("vocab_size", 10000)),
            margin=float(conf_dict.get("margin", 1.0))
        )
    else:
        from .pointwise import PointWiseModel
        model = PointWiseModel(
            representation_method=conf_dict.get("representation_method", "bow"),
            matching_method=conf_dict.get("matching_method", "cosine"),
            embedding_dim=int(conf_dict.get("embedding_dim", 100)),
            vocab_size=int(conf_dict.get("vocab_size", 10000))
        )
    
    # 这里应该加载测试数据并执行预测
    print("预测功能已设置完成")


if __name__ == '__main__':
    # 示例配置
    config = {
        "training_mode": "pairwise",
        "representation_method": "bow",
        "matching_method": "cosine",
        "embedding_dim": "100",
        "vocab_size": "10000",
        "margin": "1.0",
        "loss_type": "hinge",
        "learning_rate": "0.001"
    }
    
    print("=" * 50)
    print("训练Pair-wise模型")
    print("=" * 50)
    train(config)
    print()
    predict(config)
