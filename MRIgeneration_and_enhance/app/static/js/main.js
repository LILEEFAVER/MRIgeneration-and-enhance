$(document).ready(function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化滑块
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function createSlider(elementId, initialValue, callback) {
        const slider = document.getElementById(elementId);
        if (!slider) {
            console.error('Slider element not found:', elementId);
            return null;
        }

        try {
            noUiSlider.create(slider, {
                start: initialValue,
                connect: true,
                step: 0.1,
                range: {
                    'min': 0,
                    'max': 1
                },
                tooltips: true,
                format: {
                    to: function(value) {
                        return value.toFixed(1);
                    },
                    from: function(value) {
                        return parseFloat(value);
                    }
                }
            });

            const debouncedCallback = debounce(callback, 100);
            
            slider.noUiSlider.on('update', function(values, handle) {
                try {
                    const value = parseFloat(values[handle]);
                    if (!isNaN(value)) {
                        debouncedCallback(value);
                    }
                } catch (error) {
                    console.error('Error updating slider value:', error);
                }
            });

            return slider.noUiSlider;
        } catch (error) {
            console.error('Error creating slider:', error);
            return null;
        }
    }
    
    // 初始化步数滑块
    function createStepsSlider(elementId, initialValue, callback) {
        const slider = document.getElementById(elementId);
        if (!slider) {
            console.error('Steps slider element not found:', elementId);
            return null;
        }

        try {
            noUiSlider.create(slider, {
                start: initialValue,
                connect: true,
                step: 5,
                range: {
                    'min': 10,
                    'max': 100
                },
                tooltips: true,
                format: {
                    to: function(value) {
                        return Math.round(value);
                    },
                    from: function(value) {
                        return parseInt(value);
                    }
                }
            });

            const debouncedCallback = debounce(callback, 100);

            slider.noUiSlider.on('update', function(values, handle) {
                try {
                    const value = parseInt(values[handle]);
                    if (!isNaN(value)) {
                        debouncedCallback(value);
                    }
                } catch (error) {
                    console.error('Error updating steps slider value:', error);
                }
            });

            return slider.noUiSlider;
        } catch (error) {
            console.error('Error creating steps slider:', error);
            return null;
        }
    }
    
    // 创建所有滑块
    // 初始化性别滑块
noUiSlider.create(document.getElementById('gender-slider'), {
    start: 0,
    connect: true,
    range: {
        'min': 0,
        'max': 1
    },
    step: 1,
    pips: {
        mode: 'values',
        values: [0, 1],
        density: 100,
        format: {
            to: function(value) {
                return value === 0 ? '女性' : '男性';
            }
        }
    }
});
    
    const ageSlider = createSlider('age-slider', 0.5, function(value) {
        $('#age-value').text(value.toFixed(1));
    });
    
    const ventricularVolSlider = createSlider('ventricular-vol-slider', 0.5, function(value) {
        $('#ventricular-vol-value').text(value.toFixed(1));
    });
    
    const brainVolSlider = createSlider('brain-vol-slider', 0.5, function(value) {
        $('#brain-vol-value').text(value.toFixed(1));
    });
    
    const stepsSlider = createStepsSlider('steps-slider', 50, function(value) {
        $('#steps-value').text(value);
    });
    
    // 添加按钮悬停效果
    $('#generateBtn').hover(
        function() { $(this).addClass('pulse-animation'); },
        function() { $(this).removeClass('pulse-animation'); }
    );
    
    // 增强按钮点击事件
    $('#enhanceBtn').click(function() {
        // 获取当前文件名
        const filename = $('#downloadBtn').attr('href').replace('/download/', '');
        if (filename) {
            // 跳转到增强页面
            window.location.href = '/enhance/' + filename;
        } else {
            alert('请先生成图像或选择一个样本');
        }
    });
    
    // 生成按钮点击事件
    $('#generateBtn').click(function() {
        const params = {
            gender: parseFloat($('#gender-value').text()),
            age: parseFloat($('#age-value').text()),
            ventricular_vol: parseFloat($('#ventricular-vol-value').text()),
            brain_vol: parseFloat($('#brain-vol-value').text()),
            steps: parseInt($('#steps-value').text()),
            filename: $('#filename-input').val().trim() // 添加文件名参数
        };
        
        // 显示加载遮罩
        $('#loadingOverlay').show();
        $('#loadingMessage').text('正在执行推理命令，请稍候...');
        
        // 发送生成请求
        $.ajax({
            url: '/generate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(params),
            success: function(response) {
                if (response.success) {
                    // 验证文件是否存在
                    $.ajax({
                        url: '/api/verify_file/' + response.filename,
                        type: 'GET',
                        success: function(verifyResponse) {
                            if (verifyResponse.success) {
                                // 文件验证成功，继续处理
                                // 隐藏初始消息
                                $('#initialMessage').hide();
                                
                                // 显示结果容器
                                $('#resultContainer').show();
                                
                                // 设置成功消息
                                $('#successMessage').text(response.message);
                                
                                // 设置下载链接
                                $('#downloadBtn').attr('href', '/download/' + response.filename);
                                
                                // 设置3D查看器链接
                                $('#viewBtn').attr('href', '/view/' + response.filename);
                                
                                // 设置高级3D查看器按钮链接
                                $('#advanced3DBtn').attr('href', '/advanced_3d/' + response.filename);
                                
                                // 获取图像维度
                                $('#loadingMessage').text('正在加载图像数据...');
                                $.ajax({
                                    url: '/api/get_dimensions/' + response.filename,
                                    type: 'GET',
                                    success: function(dimResponse) {
                                        if (dimResponse.success) {
                                            const dims = dimResponse.dimensions;
                                            
                                            // 更新滑块最大值
                                            $('#axialSlice').attr('max', dims.depth - 1);
                                            $('#axialSlice').val(Math.floor(dims.depth / 2));
                                            
                                            $('#coronalSlice').attr('max', dims.height - 1);
                                            $('#coronalSlice').val(Math.floor(dims.height / 2));
                                            
                                            $('#sagittalSlice').attr('max', dims.width - 1);
                                            $('#sagittalSlice').val(Math.floor(dims.width / 2));
                                            
                                            // 更新图像视图
                                            updateImageViews(response.filename, dims);
                                        } else {
                                            console.error('获取维度失败:', dimResponse.message);
                                            // 使用默认维度
                                            updateImageViews(response.filename);
                                        }
                                    },
                                    error: function() {
                                        console.error('获取维度请求失败');
                                        // 使用默认维度
                                        updateImageViews(response.filename);
                                    }
                                });
                            } else {
                                console.error('文件验证失败:', verifyResponse.message);
                                alert('文件生成成功但验证失败: ' + verifyResponse.message);
                                
                                // 尝试重新加载样本列表，可能文件已被保存但路径不匹配
                                loadSamples();
                            }
                        },
                        error: function() {
                            console.error('文件验证请求失败');
                            alert('无法验证文件是否存在，请检查样本列表');
                            loadSamples();
                        }
                    });
                } else {
                    alert('生成失败: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    alert('请求错误: ' + errorResponse.message);
                } catch (e) {
                    alert('请求错误: ' + error);
                }
            },
            complete: function() {
                // 隐藏加载遮罩
                $('#loadingOverlay').hide();
            }
        });
    });
    
    // 更新图像视图
    function updateImageViews(filename, dims) {
        // 防止浏览器缓存
        const timestamp = new Date().getTime();
        
        // 默认索引值
        let axialIndex = 10;
        let coronalIndex = 14;
        let sagittalIndex = 10;
        
        // 如果有维度信息，使用中间切片
        if (dims) {
            axialIndex = Math.floor(dims.depth / 2);
            coronalIndex = Math.floor(dims.height / 2);
            sagittalIndex = Math.floor(dims.width / 2);
            
            // 更新滑块值
            $('#axialSlice').val(axialIndex);
            $('#coronalSlice').val(coronalIndex);
            $('#sagittalSlice').val(sagittalIndex);
        } else {
            // 使用滑块当前值
            axialIndex = $('#axialSlice').val();
            coronalIndex = $('#coronalSlice').val();
            sagittalIndex = $('#sagittalSlice').val();
        }
        
        // 显示加载中状态
        $('#axialView').attr('src', '/static/img/loading.gif');
        $('#coronalView').attr('src', '/static/img/loading.gif');
        $('#sagittalView').attr('src', '/static/img/loading.gif');
        
        // 添加错误处理和加载动画
        function loadImage(imgElement, url) {
            // 显示加载状态
            $(imgElement).css('opacity', '0.5').attr('src', '/static/img/loading.gif');
            
            const img = new Image();
            img.onload = function() {
                // 淡入效果显示新图像
                $(imgElement).fadeOut(200, function() {
                    $(this).attr('src', url).fadeIn(300).css('opacity', '1');
                });
            };
            img.onerror = function() {
                console.error("无法加载图像:", url);
                $(imgElement).fadeOut(200, function() {
                    $(this).attr('src', '/static/img/error.png').fadeIn(300).css('opacity', '1');
                });
            };
            img.src = url;
        }
        
        // 加载图像
        loadImage('#axialView', `/slices/${filename}/axial/${axialIndex}?t=${timestamp}`);
        loadImage('#coronalView', `/slices/${filename}/coronal/${coronalIndex}?t=${timestamp}`);
        loadImage('#sagittalView', `/slices/${filename}/sagittal/${sagittalIndex}?t=${timestamp}`);
        
        // 设置切片滑块事件
        $('#axialSlice').off('input').on('input', function() {
            const slice = $(this).val();
            loadImage('#axialView', `/slices/${filename}/axial/${slice}?t=${timestamp}`);
        });
        
        $('#coronalSlice').off('input').on('input', function() {
            const slice = $(this).val();
            loadImage('#coronalView', `/slices/${filename}/coronal/${slice}?t=${timestamp}`);
        });
        
        $('#sagittalSlice').off('input').on('input', function() {
            const slice = $(this).val();
            loadImage('#sagittalView', `/slices/${filename}/sagittal/${slice}?t=${timestamp}`);
        });
    }
});