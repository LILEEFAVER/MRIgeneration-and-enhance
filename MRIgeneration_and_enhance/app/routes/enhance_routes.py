from flask import render_template, request, jsonify, current_app, send_file
import os
import io
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from datetime import datetime
from . import main_bp
from app.utils.file_utils import get_output_dir, verify_file_exists, load_nifti_file
from app.utils.image_utils import create_error_image

# 导入深度学习增强模块
try:
    import cv2
    from skimage import exposure
    HAS_ENHANCE_DEPS = True
except ImportError:
    HAS_ENHANCE_DEPS = False
    current_app.logger.warning("图像增强依赖库未安装，部分功能可能不可用")

@main_bp.route('/enhance/<path:filename>')
def enhance_view(filename):
    """图像增强页面"""
    # 验证文件是否存在
    exists, _ = verify_file_exists(filename)
    if not exists:
        return render_template('error.html', message=f"文件不存在: {filename}")
    
    return render_template('enhance.html', filename=filename)

@main_bp.route('/api/enhance/preview/<path:filename>/<int:slice_idx>/<string:view_type>')
def enhance_preview(filename, slice_idx, view_type):
    """获取原始图像的切片预览"""
    try:
        # 验证文件是否存在
        exists, file_path = verify_file_exists(filename)
        if not exists:
            return send_file(create_error_image(f"文件不存在: {filename}"), mimetype='image/png')
        
        # 加载NIfTI文件
        img = nib.load(file_path)
        data = img.get_fdata()
        
        # 根据视图类型获取切片
        if view_type == 'axial':
            if slice_idx >= data.shape[2]:
                slice_idx = data.shape[2] - 1
            slice_data = data[:, :, slice_idx]
        elif view_type == 'coronal':
            if slice_idx >= data.shape[1]:
                slice_idx = data.shape[1] - 1
            slice_data = data[:, slice_idx, :]
        elif view_type == 'sagittal':
            if slice_idx >= data.shape[0]:
                slice_idx = data.shape[0] - 1
            slice_data = data[slice_idx, :, :]
        else:
            return send_file(create_error_image(f"无效的视图类型: {view_type}"), mimetype='image/png')
        
        # 创建图像
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(slice_data.T, cmap='gray')
        ax.axis('off')
        
        # 保存为图像
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close(fig)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"预览图像错误: {str(e)}")
        return send_file(create_error_image(str(e)), mimetype='image/png')

@main_bp.route('/api/enhance', methods=['POST'])
def enhance_image():
    """应用图像增强算法"""
    try:
        if not HAS_ENHANCE_DEPS:
            return jsonify({
                'success': False,
                'message': '图像增强依赖库未安装，无法执行增强操作'
            }), 400
        
        # 获取参数
        data = request.json
        filename = data.get('filename')
        method = data.get('method')
        params = data.get('params', {})
        
        # 验证文件名格式
        import re
        if not re.match(r'^[a-zA-Z0-9_]+\.nii\.gz$', filename):
            return jsonify({
                'success': False,
                'message': '文件名只能包含字母、数字和下划线'
            }), 400
        
        # 验证文件是否存在
        exists, file_path = verify_file_exists(filename)
        if not exists:
            return jsonify({
                'success': False,
                'message': f'文件不存在: {filename}'
            }), 404
        
        # 加载NIfTI文件
        img = nib.load(file_path)
        data_array = img.get_fdata()
        affine = img.affine
        
        # 应用增强算法
        enhanced_data = None
        
        if method == 'super_resolution':
            # 超分辨率增强
            scale_factor = float(params.get('scale_factor', 2.0))
            enhanced_data = apply_super_resolution(data_array, scale_factor)
        elif method == 'denoise':
            # 去噪增强
            strength = float(params.get('strength', 1.0))
            enhanced_data = apply_denoise(data_array, strength)
        elif method == 'contrast':
            # 对比度增强
            alpha = float(params.get('alpha', 1.5))
            beta = float(params.get('beta', 0.0))
            enhanced_data = apply_contrast_enhancement(data_array, alpha, beta)
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的增强方法: {method}'
            }), 400
        
        # 创建增强后的NIfTI文件
        enhanced_filename = f"{method}_{os.path.basename(filename)}"
        output_dir = get_output_dir()
        enhanced_path = os.path.join(output_dir, enhanced_filename)
        
        # 保存增强后的NIfTI文件
        enhanced_img = nib.Nifti1Image(enhanced_data, affine)
        nib.save(enhanced_img, enhanced_path)
        
        return jsonify({
            'success': True,
            'message': '图像增强成功',
            'enhanced_filename': enhanced_filename
        })
    except Exception as e:
        current_app.logger.error(f"图像增强错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'增强处理错误: {str(e)}'
        }), 500

# 超分辨率增强
def apply_super_resolution(data, scale_factor):
    """应用超分辨率增强"""
    # 初始化结果数组
    original_shape = data.shape
    new_shape = (int(original_shape[0] * scale_factor), 
                int(original_shape[1] * scale_factor), 
                int(original_shape[2] * scale_factor))
    enhanced_data = np.zeros(new_shape)
    
    # 对每个切片应用超分辨率
    for i in range(original_shape[2]):
        slice_data = data[:, :, i]
        # 使用OpenCV的resize函数进行上采样
        enhanced_slice = cv2.resize(slice_data, 
                                   (new_shape[1], new_shape[0]), 
                                   interpolation=cv2.INTER_CUBIC)
        
        # 将增强后的切片保存到结果数组
        z_indices = range(
            int(i * scale_factor),
            min(int((i + 1) * scale_factor), new_shape[2])
        )
        for j, z_idx in enumerate(z_indices):
            enhanced_data[:, :, z_idx] = enhanced_slice
    
    return enhanced_data

# 去噪增强
def apply_denoise(data, strength):
    """应用去噪增强"""
    # 初始化结果数组
    enhanced_data = np.zeros_like(data)
    
    # 对每个切片应用去噪
    for i in range(data.shape[2]):
        slice_data = data[:, :, i]
        # 使用OpenCV的非局部均值去噪
        h_param = 10 * strength  # 根据强度调整滤波强度
        enhanced_slice = cv2.fastNlMeansDenoising(
            slice_data.astype(np.uint8), 
            None, 
            h=h_param, 
            templateWindowSize=7, 
            searchWindowSize=21
        )
        enhanced_data[:, :, i] = enhanced_slice
    
    return enhanced_data

# 对比度增强
def apply_contrast_enhancement(data, alpha, beta):
    """应用对比度增强"""
    # 初始化结果数组
    enhanced_data = np.zeros_like(data)
    
    # 对每个切片应用对比度增强
    for i in range(data.shape[2]):
        slice_data = data[:, :, i]
        # 使用OpenCV的对比度增强
        enhanced_slice = cv2.convertScaleAbs(slice_data, alpha=alpha, beta=beta)
        enhanced_data[:, :, i] = enhanced_slice
    
    return enhanced_data