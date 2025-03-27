from flask import render_template, send_file, current_app, jsonify, redirect, url_for
import os
import io
import matplotlib
matplotlib.use('Agg')  # 设置后端为非交互式的Agg
import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib
from . import main_bp
from app.utils.file_utils import get_output_dir

@main_bp.route('/nifti/<path:filename>')
def get_nifti(filename):
    """获取NIfTI文件数据"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 详细日志记录
        current_app.logger.info(f"请求NIfTI文件: {filename}")
        current_app.logger.info(f"完整文件路径: {file_path}")
        
        if not os.path.exists(file_path):
            current_app.logger.error(f"文件不存在: {file_path}")
            return jsonify({'error': '文件不存在'}), 404
        
        # 确保正确的MIME类型
        mime_type = 'application/octet-stream'
        if filename.endswith('.nii.gz') or filename.endswith('.nii'):
            mime_type = 'application/x-nifti'
            
        current_app.logger.info(f"发送文件: {file_path}, MIME类型: {mime_type}")
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False
        )
    except Exception as e:
        current_app.logger.error(f"NIfTI文件访问错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/view_raw/<path:filename>')
def view_raw(filename):
    """2D切片查看器"""
    return render_template('viewers/view_raw.html', filename=filename)

@main_bp.route('/test_image')
def test_image():
    """测试图像生成 - 正弦波示例"""
    try:
        # 创建测试图像
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        
        # 生成数据
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        # 绘制主曲线
        line, = ax.plot(x, y, 'b-', label='sin(x)', linewidth=2)
        
        # 添加网格
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 设置坐标轴标签
        ax.set_xlabel('X轴 (弧度)', fontsize=12)
        ax.set_ylabel('Y轴 (振幅)', fontsize=12)
        
        # 设置标题
        ax.set_title('正弦波函数示例\n周期：2π，振幅：[-1, 1]', fontsize=14, pad=15)
        
        # 添加图例
        ax.legend(loc='upper right', fontsize=10)
        
        # 设置坐标轴范围
        ax.set_xlim(0, 10)
        ax.set_ylim(-1.2, 1.2)
        
        # 添加水平参考线
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        
        # 优化布局
        fig.tight_layout()
        
        # 保存到内存缓冲区
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"测试图像生成错误: {str(e)}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/simple_3d/<path:filename>')
def simple_3d_view(filename):
    """简化3D查看器"""
    try:
        # 获取文件路径
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            flash('文件不存在', 'error')
            return redirect(url_for('main.index'))
        
        dims = get_nifti_dimensions(file_path)
        return render_template('viewers/simple_3d_view.html', filename=filename, dimensions=dims)
    except Exception as e:
        current_app.logger.error(f"3D查看器错误: {str(e)}")
        flash('加载3D查看器时发生错误', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/view/<path:filename>')
def view(filename):
    """默认查看器 - 重定向到2D查看器"""
    return redirect(url_for('main.view_raw', filename=filename))

@main_bp.route('/advanced_3d/<path:filename>')
def advanced_3d_view(filename):
    """高级3D查看器 - 整合AMI.js和Cornerstone.js"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 尝试加载NIfTI文件以验证其有效性
        try:
            img = nib.load(file_path)
            dims = img.shape
            return render_template('viewers/advanced_3d_view.html', filename=filename, dimensions=dims)
        except Exception as e:
            current_app.logger.error(f"无法加载NIfTI文件: {str(e)}")
            return jsonify({'error': '无法加载文件'}), 500
    except Exception as e:
        current_app.logger.error(f"高级3D查看器错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    """下载NIfTI文件"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 根据文件扩展名设置正确的MIME类型
        mime_type = 'application/x-nifti' if filename.endswith('.nii.gz') else 'application/octet-stream'
        
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"文件下载错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/slices/<path:filename>/<view_type>/<int:index>')
def get_slice(filename, view_type, index):
    """获取特定切片的图像"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 详细的调试日志
        current_app.logger.info(f"请求切片 - 文件: {filename}, 视图: {view_type}, 索引: {index}")
        current_app.logger.info(f"完整文件路径: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            current_app.logger.error(f"文件不存在: {file_path}")
            
            # 创建一个错误图像
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, f"文件不存在: {filename}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            
            # 保存到缓冲区
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return send_file(buf, mimetype='image/png')
        
        # 尝试加载NIfTI文件
        try:
            img = nib.load(file_path)
            current_app.logger.info(f"成功加载NIfTI文件")
        except Exception as e:
            current_app.logger.error(f"无法加载NIfTI文件: {str(e)}")
            
            # 创建一个错误图像
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, f"无法加载文件: {str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            
            # 保存到缓冲区
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return send_file(buf, mimetype='image/png')
        
        # 获取数据
        data = img.get_fdata()
        current_app.logger.info(f"数据维度: {data.shape}")
        
        # 创建图像
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        
        # 获取数据维度
        dims = data.shape
        
        # 根据视图类型处理数据
        if view_type == 'axial' and len(dims) > 2:
            # 轴向切片
            if index >= dims[2]:
                index = dims[2] - 1
            slice_data = data[:, :, index]
            slice_data = np.rot90(slice_data)
            ax.imshow(slice_data, cmap='gray')
        elif view_type == 'coronal' and len(dims) > 1:
            # 冠状切片
            if index >= dims[1]:
                index = dims[1] - 1
            slice_data = data[:, index, :]
            slice_data = np.rot90(slice_data)
            ax.imshow(slice_data, cmap='gray')
        elif view_type == 'sagittal' and len(dims) > 0:
            # 矢状切片
            if index >= dims[0]:
                index = dims[0] - 1
            slice_data = data[index, :, :]
            slice_data = np.rot90(slice_data)
            ax.imshow(slice_data, cmap='gray')
        else:
            current_app.logger.error(f"无效的视图类型: {view_type} 或维度不足")
            ax.text(0.5, 0.5, f"无效的视图类型: {view_type} 或维度不足", 
                   ha='center', va='center', transform=ax.transAxes)
        
        # 关闭坐标轴
        ax.axis('off')
        fig.tight_layout(pad=0)
        
        # 将图像保存到内存缓冲区
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"切片生成错误: {str(e)}")
        # 返回一个简单的错误图像
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.text(0.5, 0.5, f'加载错误: {str(e)}', 
                horizontalalignment='center', verticalalignment='center')
        ax.axis('off')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return send_file(buf, mimetype='image/png')

@main_bp.route('/api/slice/<path:filename>/<int:slice_idx>/<string:view_type>')
def api_get_slice(filename, slice_idx, view_type):
    """API接口：获取特定切片的图像"""
    try:
        output_dir = get_output_dir()
        file_path = os.path.join(output_dir, filename)
        
        # 详细的调试日志
        current_app.logger.info(f"API请求切片 - 文件: {filename}, 视图: {view_type}, 索引: {slice_idx}")
        current_app.logger.info(f"完整文件路径: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            current_app.logger.error(f"文件不存在: {file_path}")
            
            # 创建一个错误图像
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, f"文件不存在: {filename}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            
            # 保存到缓冲区
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return send_file(buf, mimetype='image/png')
        
        # 尝试加载NIfTI文件
        try:
            img = nib.load(file_path)
            current_app.logger.info(f"成功加载NIfTI文件")
        except Exception as e:
            current_app.logger.error(f"无法加载NIfTI文件: {str(e)}")
            
            # 创建一个错误图像
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.text(0.5, 0.5, f"无法加载文件: {str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
            
            # 保存到缓冲区
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)
            
            return send_file(buf, mimetype='image/png')
        
        # 获取数据
        data = img.get_fdata()
        current_app.logger.info(f"数据维度: {data.shape}")
        
        # 创建图像
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        
        # 获取数据维度
        dims = data.shape
        
        # 根据视图类型处理数据
        if view_type == 'axial' and len(dims) > 2:
            # 轴向切片
            if slice_idx >= dims[2]:
                slice_idx = dims[2] - 1
            slice_data = data[:, :, slice_idx]
            ax.imshow(slice_data.T, cmap='gray')
        elif view_type == 'coronal' and len(dims) > 1:
            # 冠状切片
            if slice_idx >= dims[1]:
                slice_idx = dims[1] - 1
            slice_data = data[:, slice_idx, :]
            ax.imshow(slice_data, cmap='gray')
        elif view_type == 'sagittal' and len(dims) > 0:
            # 矢状切片
            if slice_idx >= dims[0]:
                slice_idx = dims[0] - 1
            slice_data = data[slice_idx, :, :]
            ax.imshow(slice_data, cmap='gray')
        else:
            current_app.logger.error(f"无效的视图类型: {view_type} 或维度不足")
            ax.text(0.5, 0.5, f"无效的视图类型: {view_type} 或维度不足", 
                   ha='center', va='center', transform=ax.transAxes)
        
        # 关闭坐标轴
        ax.axis('off')
        fig.tight_layout(pad=0)
        
        # 将图像保存到内存缓冲区
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
        buf.seek(0)
        plt.close(fig)
        
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"切片生成错误: {str(e)}")
        # 返回一个简单的错误图像
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.text(0.5, 0.5, f'加载错误: {str(e)}', 
                horizontalalignment='center', verticalalignment='center')
        ax.axis('off')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return send_file(buf, mimetype='image/png')