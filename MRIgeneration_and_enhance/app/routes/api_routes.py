from flask import jsonify, current_app
import os
from datetime import datetime
import nibabel as nib
from . import main_bp
from app.utils.file_utils import get_output_dir

@main_bp.route('/api/list_samples')
def list_samples():
    """列出output目录中的所有样本"""
    try:
        output_dir = get_output_dir()
        
        # 获取所有.nii.gz文件
        samples = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')]
        
        return jsonify({
            'success': True,
            'samples': samples
        })
    except Exception as e:
        current_app.logger.error(f"列出样本错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main_bp.route('/api/get_dimensions/<path:filename>')
def get_dimensions(filename):
    """获取NIfTI文件的维度信息"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在: {filename}'
            }), 404
        
        # 加载NIfTI文件
        img = nib.load(file_path)
        data = img.get_fdata()
        
        # 获取维度
        dims = data.shape
        
        # 获取值范围
        value_min = float(data.min())
        value_max = float(data.max())
        
        # 获取像素类型
        dtype = str(data.dtype)
        
        return jsonify({
            'success': True,
            'dimensions': {
                'width': int(dims[0]),
                'height': int(dims[1]),
                'depth': int(dims[2]) if len(dims) > 2 else 1,
                'channels': int(dims[3]) if len(dims) > 3 else 1
            },
            'metadata': {
                'value_range': [value_min, value_max],
                'dtype': dtype,
                'affine': img.affine.tolist() if hasattr(img, 'affine') else None,
                'header_info': {
                    'pixdim': [float(x) for x in img.header.get_zooms()] if hasattr(img, 'header') else None
                }
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取维度信息错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@main_bp.route('/api/verify_file/<path:filename>')
def verify_file(filename):
    """验证文件是否存在并可读取"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在: {file_path}'
            })
        
        # 尝试读取文件
        img = nib.load(file_path)
        shape = img.shape
        
        return jsonify({
            'success': True,
            'message': '文件存在且可读取',
            'path': file_path,
            'shape': [int(x) for x in shape]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文件验证错误: {str(e)}'
        })

@main_bp.route('/api/debug/files')
def debug_files():
    """列出输出目录中所有文件的详细信息"""
    try:
        output_dir = get_output_dir()
        
        # 检查目录是否存在
        if not os.path.exists(output_dir):
            return jsonify({
                'success': False,
                'message': f'输出目录不存在: {output_dir}'
            })
        
        # 获取所有文件信息
        files_info = []
        for filename in os.listdir(output_dir):
            if filename.endswith('.nii.gz') or filename.endswith('.nii'):
                file_path = os.path.join(output_dir, filename)
                stats = os.stat(file_path)
                
                # 尝试读取文件
                readable = True
                dimensions = None
                try:
                    img = nib.load(file_path)
                    dimensions = img.shape
                except Exception as e:
                    readable = False
                    
                files_info.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stats.st_size,
                    'creation_time': datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modification_time': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'readable': readable,
                    'dimensions': dimensions
                })
        
        return jsonify({
            'success': True,
            'output_directory': output_dir,
            'files_count': len(files_info),
            'files': files_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文件信息失败: {str(e)}'
        })

@main_bp.route('/api/debug/paths')
def debug_paths():
    """显示重要的路径信息"""
    try:
        output_dir = get_output_dir()
        
        # 获取当前工作目录
        cwd = os.getcwd()
        
        # 检查输出目录是否存在
        output_exists = os.path.exists(output_dir)
        
        # 检查目录权限
        output_writable = os.access(output_dir, os.W_OK) if output_exists else False
        
        # 相对于当前工作目录的路径
        rel_path = os.path.relpath(output_dir, cwd)
        
        # 列出输出目录中的文件（如果存在）
        files = []
        if output_exists:
            files = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')]
        
        return jsonify({
            'success': True,
            'current_working_directory': cwd,
            'output_directory': {
                'absolute_path': output_dir,
                'relative_path': rel_path,
                'exists': output_exists,
                'writable': output_writable,
                'files_count': len(files),
                'nii_files': files
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取路径信息失败: {str(e)}'
        })

# 其他API路由... 