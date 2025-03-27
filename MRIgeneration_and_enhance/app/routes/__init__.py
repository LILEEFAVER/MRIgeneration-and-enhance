from flask import Blueprint

# 创建蓝图
main_bp = Blueprint('main', __name__)

# 在导入这些模块前，确保它们已经创建
# 如果这些文件不存在，请先注释掉这些导入语句，防止启动错误
# 创建文件后再取消注释

# from . import main_routes
# from . import viewer_routes
# from . import api_routes 

# 现在导入路由模块 (取消注释)
from . import main_routes
from . import viewer_routes
from . import api_routes
from . import enhance_routes