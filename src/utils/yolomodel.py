from ultralytics import YOLO
from typing import List, Any
import numpy as np

    # 子进程初始化时加载模型
global model
model = YOLO('best copy 3.pt')
model.to('cuda')

def batch_predict(frames: List[np.ndarray]) -> List[Any]:
    # 批量推理接口
    return model(frames)