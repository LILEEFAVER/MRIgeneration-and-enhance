// 增强模块的JavaScript代码

// 全局变量
let currentFilename = '';
let currentView = 'axial';
let currentSlice = 10;
let maxSlices = {
    'axial': 144,  // 145-1，因为索引从0开始
    'coronal': 213, // 214-1，因为索引从0开始
    'sagittal': 149   // 149-1，因为索引从0开始
};
let enhancedFilename = null;

// 初始化页面
$(document).ready(function() {
    // 获取当前文件名
    currentFilename = window.location.pathname.split('/').pop();
    
    // 初始化滑块
    initSliders();
    
    // 加载原始图像
    updateOriginalImage();
    
    // 绑定事件
    bindEvents();
});

// 初始化所有滑块
function initSliders() {
    // 超分辨率 - 放大倍数滑块
    const scaleFactorSlider = document.getElementById('scale-factor-slider');
    if (scaleFactorSlider) {
        noUiSlider.create(scaleFactorSlider, {
            start: [2.0],
            connect: true,
            step: 0.1,
            range: {
                'min': [1.0],
                'max': [4.0]
            }
        });
        
        scaleFactorSlider.noUiSlider.on('update', function(values) {
            document.getElementById('scale-factor-value').textContent = parseFloat(values[0]).toFixed(1);
        });
    }
    
    // 去噪 - 强度滑块
    const denoiseStrengthSlider = document.getElementById('denoise-strength-slider');
    if (denoiseStrengthSlider) {
        noUiSlider.create(denoiseStrengthSlider, {
            start: [1.0],
            connect: true,
            step: 0.1,
            range: {
                'min': [0.1],
                'max': [2.0]
            }
        });
        
        denoiseStrengthSlider.noUiSlider.on('update', function(values) {
            document.getElementById('denoise-strength-value').textContent = parseFloat(values[0]).toFixed(1);
        });
    }
    
    // 对比度 - alpha滑块
    const contrastAlphaSlider = document.getElementById('contrast-alpha-slider');
    if (contrastAlphaSlider) {
        noUiSlider.create(contrastAlphaSlider, {
            start: [1.5],
            connect: true,
            step: 0.1,
            range: {
                'min': [0.5],
                'max': [3.0]
            }
        });
        
        contrastAlphaSlider.noUiSlider.on('update', function(values) {
            document.getElementById('contrast-alpha-value').textContent = parseFloat(values[0]).toFixed(1);
        });
    }
    
    // 对比度 - beta滑块
    const contrastBetaSlider = document.getElementById('contrast-beta-slider');
    if (contrastBetaSlider) {
        noUiSlider.create(contrastBetaSlider, {
            start: [0.0],
            connect: true,
            step: 0.05,
            range: {
                'min': [-0.5],
                'max': [0.5]
            }
        });
        
        contrastBetaSlider.noUiSlider.on('update', function(values) {
            document.getElementById('contrast-beta-value').textContent = parseFloat(values[0]).toFixed(2);
        });
    }
    
    // 切片滑块
    const sliceSlider = document.getElementById('sliceSlider');
    if (sliceSlider) {
        sliceSlider.addEventListener('input', function() {
            currentSlice = parseInt(this.value);
            document.getElementById('slicePosition').textContent = currentSlice;
            updateOriginalImage();
        });
    }
}

// 绑定事件
function bindEvents() {
    // 增强方法切换
    $('#enhanceMethod').change(function() {
        const method = $(this).val();
        $('.method-params').hide();
        $(`#${method}_params`).show();
    });
    
    // 视图类型切换
    $('#viewType').change(function() {
        currentView = $(this).val();
        updateSliceRange();
        updateOriginalImage();
    });
    
    // 应用增强按钮
    $('#enhanceBtn').click(function() {
        applyEnhancement();
    });
    
    // 下载增强图像按钮
    $('#downloadEnhancedBtn').click(function(e) {
        e.preventDefault();
        if (enhancedFilename) {
            window.location.href = `/download/${enhancedFilename}`;
        }
    });
    
    // 查看完整增强图像按钮
    $('#viewEnhancedBtn').click(function(e) {
        e.preventDefault();
        if (enhancedFilename) {
            window.location.href = `/view/${enhancedFilename}`;
        }
    });
}

// 更新切片滑块范围
function updateSliceRange() {
    const sliceSlider = document.getElementById('sliceSlider');
    if (sliceSlider) {
        sliceSlider.max = maxSlices[currentView];
        if (currentSlice > maxSlices[currentView]) {
            currentSlice = Math.floor(maxSlices[currentView] / 2);
            sliceSlider.value = currentSlice;
            document.getElementById('slicePosition').textContent = currentSlice;
            updateOriginalImage();
            updateEnhancedImage();
        }
    }
}

// 更新原始图像
function updateOriginalImage() {
    const imageUrl = `/api/enhance/preview/${currentFilename}/${currentSlice}/${currentView}`;
    const img = $('#originalImage');
    img.attr('src', imageUrl + '?t=' + new Date().getTime());
    
    // 应用图像变换
    if (currentView === 'coronal' || currentView === 'sagittal') {
        img.css('transform', 'scale(-1, 1) rotate(180deg)');
    } else {
        img.css('transform', 'none');
    }
}

// 更新增强后的图像
function updateEnhancedImage() {
    if (enhancedFilename) {
        const imageUrl = `/api/slice/${enhancedFilename}/${currentSlice}/${currentView}?t=${new Date().getTime()}`;
        const img = $('<img>', {
            src: imageUrl,
            alt: '增强图像',
            class: 'img-fluid'
        });
        
        // 应用图像变换
        if (currentView === 'coronal' || currentView === 'sagittal') {
            img.css('transform', 'rotate(-90deg)');
        }
        
        $('#enhancedImageContainer').empty().append(img);
    }
}

// 监听切片和视图变化
$('#sliceSlider').on('input', function() {
    currentSlice = parseInt(this.value);
    document.getElementById('slicePosition').textContent = currentSlice;
    updateOriginalImage();
    updateEnhancedImage();
});

$('#viewType').change(function() {
    currentView = $(this).val();
    updateSliceRange();
});

// 应用增强
function applyEnhancement() {
    // 显示加载动画
    $('#loadingOverlay').show();
    $('#loadingMessage').text('正在应用增强算法...');
    
    // 获取当前选择的方法和参数
    const method = $('#enhanceMethod').val();
    let params = {};
    
    // 根据不同方法获取参数
    if (method === 'super_resolution') {
        params.scale_factor = parseFloat($('#scale-factor-value').text());
    } else if (method === 'denoise') {
        params.strength = parseFloat($('#denoise-strength-value').text());
    } else if (method === 'contrast') {
        params.alpha = parseFloat($('#contrast-alpha-value').text());
        params.beta = parseFloat($('#contrast-beta-value').text());
    }
    
    // 发送增强请求
    $.ajax({
        url: '/api/enhance',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            filename: currentFilename,
            method: method,
            params: params
        }),
        success: function(response) {
            $('#loadingOverlay').hide();
            
            if (response.success) {
                // 更新增强状态
                $('#enhancedStatus').removeClass('bg-secondary').addClass('bg-success').text('已增强');
                
                // 保存增强后的文件名
                enhancedFilename = response.enhanced_filename;
                
                // 显示增强后的图像
                const enhancedImageHtml = `<img src="/api/slice/${enhancedFilename}/${currentSlice}/${currentView}?t=${new Date().getTime()}" alt="增强图像" class="img-fluid">`;
                $('#enhancedImageContainer').html(enhancedImageHtml);
                
                // 显示控制按钮
                $('#enhancedControls').show();
                
                // 更新增强信息
                let methodName = '';
                let paramInfo = '';
                
                if (method === 'super_resolution') {
                    methodName = '超分辨率';
                    paramInfo = `放大倍数: ${params.scale_factor}`;
                } else if (method === 'denoise') {
                    methodName = '去噪';
                    paramInfo = `强度: ${params.strength}`;
                } else if (method === 'contrast') {
                    methodName = '对比度增强';
                    paramInfo = `Alpha: ${params.alpha}, Beta: ${params.beta}`;
                }
                
                $('#enhancedInfo').html(`<strong>增强方法:</strong> ${methodName}<br><strong>参数:</strong> ${paramInfo}`);
                
                // 更新增强状态
                $('#enhancedStatus').removeClass('bg-secondary').addClass('bg-success').text('已增强');
                
                // 保存增强后的文件名
                enhancedFilename = response.enhanced_filename;
                
                // 显示增强后的图像并更新预览
                updateEnhancedImage();
                
                // 显示控制按钮
                $('#enhancedControls').show();
            } else {
                $('#enhancedStatus').removeClass('bg-success').addClass('bg-secondary').text('未增强');
                alert('增强失败: ' + response.message);
            }
        },
        error: function(xhr, status, error) {
            $('#loadingOverlay').hide();
            $('#enhancedStatus').removeClass('bg-success').addClass('bg-secondary').text('未增强');
            alert('增强请求失败: ' + error);
        }
    });
}