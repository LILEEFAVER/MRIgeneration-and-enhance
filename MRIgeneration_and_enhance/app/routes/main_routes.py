from flask import render_template, request, jsonify, current_app
import os
import subprocess
from datetime import datetime
import time
from . import main_bp
from app.utils.file_utils import get_output_dir

@main_bp.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@main_bp.route('/generate', methods=['POST'])
def generate():
    """处理生成MRI的请求"""
    try:
        # 获取参数
        data = request.json
        gender = float(data.get('gender', 0.5))
        age = float(data.get('age', 0.5))
        ventricular_vol = float(data.get('ventricular_vol', 0.5))
        brain_vol = float(data.get('brain_vol', 0.5))
        steps = int(data.get('steps', 50))
        custom_filename = data.get('filename', '').strip()
        
        # 获取当前时间（用于比较文件创建时间）
        start_time = datetime.now()
        current_app.logger.info(f"开始执行时间: {start_time}")
        
        # 获取输出目录
        output_dir = get_output_dir()
        current_app.logger.info(f"使用输出目录: {output_dir}")
        
        # 获取执行前的文件列表
        before_files = set([f for f in os.listdir(output_dir) if f.endswith('.nii.gz')])
        current_app.logger.info(f"执行前nii.gz文件数量: {len(before_files)}")
        
        # 构建命令 - 添加所有参数
        cmd = [
            "python", "-m", "monai.bundle", "run", "save_nii",
            "--config_file", "configs/inference.json",
            "--gender", str(gender),
            "--age", str(age),
            "--ventricular_vol", str(ventricular_vol),
            "--brain_vol", str(brain_vol)
        ]
        
        # 如果需要设置步数，可以在命令中添加覆盖参数
        if steps != 50:  # 只在不是默认值时添加
            cmd.extend(["--set_timesteps", f"$@scheduler.set_timesteps(num_inference_steps={steps})"])
        
        # 执行命令
        current_app.logger.info(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        # 检查命令是否成功执行
        if process.returncode != 0:
            error_msg = stderr.decode()
            current_app.logger.error(f"命令执行失败: {error_msg}")
            return jsonify({
                'success': False,
                'message': f'推理失败: {error_msg}'
            }), 500
        
        # 等待一小段时间确保文件写入完成
        time.sleep(1)
        
        # 获取执行后的文件列表
        after_files = set([f for f in os.listdir(output_dir) if f.endswith('.nii.gz')])
        current_app.logger.info(f"执行后nii.gz文件数量: {len(after_files)}")
        
        # 找出新增的文件
        new_files = after_files - before_files
        current_app.logger.info(f"新增nii.gz文件: {new_files}")
        
        if new_files:
            # 使用新生成的文件
            filename = list(new_files)[0]
            current_app.logger.info(f"使用新生成的文件: {filename}")
            
            # 如果用户指定了文件名，重命名文件
            if custom_filename:
                # 确保文件名以.nii.gz结尾
                if not custom_filename.endswith('.nii.gz'):
                    custom_filename += '.nii.gz'
                
                old_path = os.path.join(output_dir, filename)
                new_path = os.path.join(output_dir, custom_filename)
                
                # 如果目标文件已存在，添加时间戳
                if os.path.exists(new_path):
                    timestamp = datetime.now().strftime("%H%M%S_%d%m%Y")
                    custom_filename = f"{os.path.splitext(custom_filename)[0]}_{timestamp}.nii.gz"
                    new_path = os.path.join(output_dir, custom_filename)
                
                os.rename(old_path, new_path)
                filename = custom_filename
                current_app.logger.info(f"文件已重命名为: {filename}")
        else:
            # 如果没有发现新文件，尝试查找最近修改的文件
            all_nii_files = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')]
            if all_nii_files:
                all_nii_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)
                filename = all_nii_files[0]
                current_app.logger.info(f"未找到新文件，使用最近修改的文件: {filename}")
            else:
                return jsonify({
                    'success': False,
                    'message': '推理成功但未找到任何.nii.gz文件'
                }), 500
        
        # 确认文件是否存在
        file_path = os.path.join(output_dir, filename)
        if not os.path.exists(file_path):
            current_app.logger.error(f"找到的文件不存在: {file_path}")
            return jsonify({
                'success': False,
                'message': f'找到了文件名但文件不存在: {filename}'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '脑部MRI生成成功',
            'file_path': file_path,
            'filename': filename
        })
    except Exception as e:
        current_app.logger.error(f"生成过程出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        }), 500