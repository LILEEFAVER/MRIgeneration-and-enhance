# API 文档

## 模型训练接口
```python
class LatentDiffusionTrainer:
    def __init__(self, 
                 dataset: BraTS2023Dataset,
                 model_config: Dict,
                 optimizer: torch.optim.Optimizer = AdamW,
                 mixed_precision: bool = True):
        """
        :param dataset: 预处理的3D MRI数据集
        :param model_config: 模型超参数配置
        :param optimizer: 优化器类型（默认AdamW）
        :param mixed_precision: 是否启用混合精度训练
        """

## 推理流程参数
```json
{
  "sampling_steps": 50,
  "guidance_scale": 7.5,
  "output_resolution": "256x256x256",
  "post_processing": {
    "normalization": "z-score",
    "intensity_range": [0, 1]
  }
}
```

## 医疗数据处理接口
```python
def convert_dicom_to_nifti(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    skip_duplicates: bool = True,
    anonymize: bool = False
) -> ConversionReport:
    """
    :param input_path: DICOM目录或文件路径
    :param output_dir: NIfTI输出目录
    :param skip_duplicates: 跳过重复序列
    :param anonymize: 匿名化患者信息
    :return: 包含转换统计信息的报告对象
    """
```

## RESTful API 接口说明

### 生成图像接口
`POST /api/v1/generate`
**请求参数**:
```json
{
  "guidance_scale": 7.5,
  "steps": 50,
  "resolution": "256x256x256"
}
```
**响应示例**:
```json
{
  "task_id": "5f4d87d2-b",
  "estimated_time": 28
}
```

### 图像增强接口
`POST /api/v1/enhance`
**请求参数**:
```json
{
  "task_id": "5f4d87d2-b",
  "operations": ["super_resolution", "denoise"]
}
```

### 结果下载接口
`GET /api/v1/download/{task_id}`
**响应头**:
```
Content-Type: application/nifti
Content-Disposition: attachment; filename="result.nii.gz"
```

## 错误代码表
| 代码 | 描述                  | 解决方案指引               |
|------|-----------------------|--------------------------|
| 4001 | DICOM元数据缺失       | 检查DICOM文件完整性       |
| 5003 | 显存不足              | 降低batch_size或分辨率   |
| 6002 | 无效的生成参数组合    | 参考参数范围说明文档      |