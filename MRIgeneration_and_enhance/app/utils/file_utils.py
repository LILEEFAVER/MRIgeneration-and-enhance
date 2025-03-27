import os
import nibabel as nib
from flask import current_app

def get_output_dir():
    """获取输出目录"""
    return os.path.join(os.getcwd(), "output")

def verify_file_exists(filename, output_dir=None):
    """验证文件是否存在"""
    if output_dir is None:
        output_dir = get_output_dir()
    file_path = os.path.join(output_dir, filename)
    return os.path.exists(file_path), file_path

def load_nifti_file(filename):
    """加载NIfTI文件"""
    file_path = os.path.join(get_output_dir(), filename)
    return nib.load(file_path) 