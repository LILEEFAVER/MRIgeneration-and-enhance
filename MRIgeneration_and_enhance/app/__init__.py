from flask import Flask
import logging.config
import os

def create_app(config_name='default'):
    """创建和配置Flask应用"""
    app = Flask(__name__)
    
    # 配置日志
    logging.config.fileConfig('configs/logging.conf')
    logger = logging.getLogger(__name__)
    logger.info("启动脑部MRI生成系统")
    
    # 确保MONAI可用
    try:
        import monai
        logger.info(f"MONAI版本: {monai.__version__}")
    except ImportError:
        logger.error("MONAI未安装，请安装MONAI库")
        import sys
        sys.exit(1)
    
    # 确保输出目录存在
    from app.utils.file_utils import get_output_dir
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    
    # 注册蓝图
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # 配置模板自动重新加载
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    return app