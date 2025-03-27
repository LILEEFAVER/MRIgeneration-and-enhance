import io
import matplotlib.pyplot as plt

def create_error_image(error_message):
    """创建包含错误信息的图像"""
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.text(0.5, 0.5, error_message, 
            horizontalalignment='center', verticalalignment='center',
            wrap=True)
    ax.axis('off')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf 