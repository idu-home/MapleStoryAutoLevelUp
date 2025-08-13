// 连接WebSocket
const socket = io();

// 检测设备类型和发送客户端信息
function detectDevice() {
    const userAgent = navigator.userAgent;
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
    const devicePixelRatio = window.devicePixelRatio || 1;
    const screenWidth = window.screen.width;
    const screenHeight = window.screen.height;
    
    return {
        is_mobile: isMobile,
        device_pixel_ratio: devicePixelRatio,
        screen_width: screenWidth,
        screen_height: screenHeight,
        user_agent: userAgent,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight
    };
}

// DOM元素
const connectionDot = document.getElementById('connection-dot');
const connectionStatus = document.getElementById('connection-status');
const debugImage = document.getElementById('debug-image');
const debugPlaceholder = document.getElementById('debug-placeholder');
const debugInfo = document.getElementById('debug-info');
const routeImage = document.getElementById('route-image');
const routePlaceholder = document.getElementById('route-placeholder');
const routeInfo = document.getElementById('route-info');
const fpsText = document.getElementById('fps-text');
const latencyText = document.getElementById('latency-text');
const encodeText = document.getElementById('encode-text');
const qualityText = document.getElementById('quality-text');
const scenarioInfo = document.getElementById('scenario-info');
const scenarioTitle = document.getElementById('scenario-title');
const scenarioMessage = document.getElementById('scenario-message');
const scenarioDescription = document.getElementById('scenario-description');

// FPS计算
let frameCount = 0;
let lastFpsTime = Date.now();
let fps = 0;

// 连接状态处理
socket.on('connect', function() {
    console.log('🔗 WebSocket connected');
    connectionDot.classList.add('connected');
    connectionStatus.textContent = '已连接';
    debugInfo.textContent = '状态: 已连接，等待图像...';
    routeInfo.textContent = '状态: 已连接，等待图像...';
    
    // 发送客户端设备信息以进行优化
    const deviceInfo = detectDevice();
    socket.emit('client_info', deviceInfo);
    console.log('📱 Device info sent:', deviceInfo);
    
    // 更新设备状态显示
    const deviceStatus = document.getElementById('device-status');
    deviceStatus.textContent = `📱 设备: ${deviceInfo.is_mobile ? '移动端' : '桌面端'} (${deviceInfo.screen_width}x${deviceInfo.screen_height})`;
    deviceStatus.style.color = deviceInfo.is_mobile ? '#ff9800' : '#4CAF50';
});

socket.on('disconnect', function() {
    connectionDot.classList.remove('connected');
    connectionStatus.textContent = '连接断开';
    debugInfo.textContent = '状态: 连接断开';
    routeInfo.textContent = '状态: 连接断开';
});

// 状态消息
socket.on('status', function(data) {
    console.log('Status:', data.message);
});

// 调试图像更新
socket.on('debug_frame_update', function(data) {
    if (data.debug_frame) {
        debugImage.src = data.debug_frame;
        debugImage.style.display = 'block';
        debugPlaceholder.style.display = 'none';
        
        const now = Date.now();
        const serverTime = data.timestamp * 1000; // Convert to milliseconds
        // 计算总延迟：包括服务端处理时间 + 网络传输时间 + WebSocket传输时间
        const totalLatency = Math.round(now - serverTime); 
        
        // 如果有服务端处理时间信息，计算网络延迟
        let networkLatency = totalLatency;
        if (data.performance && data.performance.frame_time_ms) {
            networkLatency = Math.max(0, totalLatency - Math.round(data.performance.frame_time_ms));
        }
        
        debugInfo.textContent = `状态: 已更新 (${new Date().toLocaleTimeString()}) - 延迟: ${totalLatency}ms`;
        
        // 更新性能指标
        frameCount++;
        if (now - lastFpsTime >= 1000) {
            fps = frameCount;
            frameCount = 0;
            lastFpsTime = now;
        }
        fpsText.querySelector('.metric-number').textContent = fps.toString().padStart(2, ' ');
        // 显示网络延迟，更准确反映实际网络传输延迟
        latencyText.querySelector('.metric-number').textContent = networkLatency.toString().padStart(3, ' ');
        
        // 显示编码时间和其他性能指标（如果可用）
        if (data.performance && data.performance.encode_time_ms) {
            const encodeTime = Math.round(data.performance.encode_time_ms);
            encodeText.querySelector('.metric-number').textContent = encodeTime.toString().padStart(2, ' ');
        }
        
        // 显示图像质量信息
        if (data.quality) {
            qualityText.querySelector('.metric-number').textContent = data.quality.toString().padStart(3, ' ');
        }
        
        // 延迟警告 (基于网络延迟)
        if (networkLatency > 100) {
            latencyText.style.color = '#ff4444'; // 红色表示高延迟
        } else if (networkLatency > 50) {
            latencyText.style.color = '#ffaa00'; // 橙色表示中等延迟
        } else {
            latencyText.style.color = '#4CAF50'; // 绿色表示低延迟
        }
    }
});

// 路线图像更新
socket.on('route_frame_update', function(data) {
    if (data.route_frame) {
        routeImage.src = data.route_frame;
        routeImage.style.display = 'block';
        routePlaceholder.style.display = 'none';
        routeInfo.textContent = `状态: 已更新 (${new Date().toLocaleTimeString()})`;
    }
});


// Bot状态实时更新 - WebSocket推送
socket.on('bot_status_update', function(data) {
    console.log('Real-time bot status update:', data);
    updateBotStatus(data.bot_status, data.bot_state);
    
    // 更新健康状态
    if (data.health_stats) {
        updateHealthStats(data.health_stats);
    }
    
    // 显示EXP追踪调试信息
    if (data.exp_debug_info) {
        updateExpDebugInfo(data.exp_debug_info);
        
        // 检查是否有新的快照，如果有则更新图表
        checkForNewSnapshots(data.exp_debug_info);
    }
});


// 错误处理
socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
    connectionStatus.textContent = '连接错误';
    connectionDot.classList.remove('connected');
});

// 图像加载错误处理
debugImage.onerror = function() {
    debugInfo.textContent = '状态: 图像加载失败';
};

routeImage.onerror = function() {
    routeInfo.textContent = '状态: 图像加载失败';
};


// 切换优化模式
async function toggleOptimization() {
    try {
        const response = await fetch('/api/toggle_optimization', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        if (result.success) {
            updateOptimizationStatus(result.optimized_encoding);
            console.log('Optimization mode toggled:', result.optimized_encoding);
        } else {
            console.error('Failed to toggle optimization:', result.error);
        }
    } catch (error) {
        console.error('Error toggling optimization:', error);
    }
}

// 更新优化状态显示
function updateOptimizationStatus(isOptimized) {
    const optimizationStatus = document.getElementById('optimization-status');
    if (isOptimized) {
        optimizationStatus.textContent = '🚀 优化模式: 开启';
        optimizationStatus.style.color = '#4CAF50';
    } else {
        optimizationStatus.textContent = '🚀 优化模式: 关闭';
        optimizationStatus.style.color = '#888';
    }
}

// Bot控制函数
let currentBotStatus = 'unknown';

async function stopBot() {
    const botStopBtn = document.getElementById('bot-stop-btn');
    
    // 禁用按钮，防止重复点击
    botStopBtn.disabled = true;
    
    try {
        const response = await fetch('/api/bot/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('Bot stopped successfully');
        } else {
            console.error('Failed to stop bot:', result.error);
            alert('停止Bot失败: ' + result.error);
        }
        
        // 立即更新状态
        fetchServerStatus();
        
    } catch (error) {
        console.error('Error stopping bot:', error);
        alert('停止Bot时出错: ' + error.message);
    } finally {
        // 重新启用按钮
        setTimeout(() => {
            botStopBtn.disabled = false;
        }, 1000);
    }
}

// 更新Bot状态显示
function updateBotStatus(botStatus, botState) {
    // 避免重复更新相同状态
    if (currentBotStatus === botStatus && 
        document.getElementById('bot-state-text') && 
        document.getElementById('bot-state-text').textContent === `State: ${botState}`) {
        return;
    }
    
    currentBotStatus = botStatus;  // 更新全局状态
    
    const botStatusElement = document.getElementById('bot-status');
    const botStatusText = document.getElementById('bot-status-text');
    const botStateText = document.getElementById('bot-state-text');
    const botStopBtn = document.getElementById('bot-stop-btn');
    
    // 清除所有状态类
    if (botStatusElement) {
        botStatusElement.className = 'bot-status';
    }
    
    // 添加状态变化闪烁效果
    if (botStatusElement) {
        botStatusElement.style.transition = 'background-color 0.3s ease';
        botStatusElement.style.backgroundColor = '#444';
        setTimeout(() => {
            botStatusElement.style.backgroundColor = '';
        }, 300);
    }
    
    // 根据状态设置样式和按钮状态
    switch (botStatus) {
        case 'running':
            if (botStatusElement) {
                botStatusElement.classList.add('running');
                botStatusText.textContent = 'Bot: 运行中';
            }
            if (botStopBtn) {
                botStopBtn.disabled = false;
                botStopBtn.textContent = '⏹️ 停止Bot';
                botStopBtn.style.opacity = '1';
            }
            break;
        case 'paused':
        case 'stopped':
            if (botStatusElement) {
                botStatusElement.classList.add('paused');
                botStatusText.textContent = 'Bot: 已停止';
            }
            if (botStopBtn) {
                botStopBtn.disabled = true;
                botStopBtn.textContent = '⏹️ Bot已停止';
                botStopBtn.style.opacity = '0.6';
            }
            break;
        default:
            if (botStatusElement) {
                botStatusText.textContent = 'Bot: 未知状态';
            }
            if (botStopBtn) {
                botStopBtn.disabled = true;
                botStopBtn.style.opacity = '0.6';
            }
    }
    
    // 更新状态文本
    if (botStateText) {
        if (botState && botState !== 'unknown') {
            botStateText.textContent = `State: ${botState}`;
        } else {
            botStateText.textContent = 'State: --';
        }
    }
}

// 更新健康状态显示
function updateHealthStats(healthStats) {
    const hpText = document.getElementById('hp-text');
    const mpText = document.getElementById('mp-text');
    const expText = document.getElementById('exp-text');
    
    if (hpText && healthStats.hp_percent !== null && healthStats.hp_percent !== undefined) {
        const hpValue = Math.round(healthStats.hp_percent * 10) / 10; // 保留1位小数
        hpText.querySelector('.metric-number').textContent = hpValue.toFixed(1).padStart(5, ' ');
        
        // HP颜色警告
        const hpColor = hpValue > 70 ? '#4CAF50' : hpValue > 30 ? '#ffaa00' : '#ff4444';
        hpText.querySelector('.metric-number').style.color = hpColor;
    } else if (hpText) {
        hpText.querySelector('.metric-number').textContent = '--';
        hpText.querySelector('.metric-number').style.color = '#888';
    }
    
    if (mpText && healthStats.mp_percent !== null && healthStats.mp_percent !== undefined) {
        const mpValue = Math.round(healthStats.mp_percent * 10) / 10;
        mpText.querySelector('.metric-number').textContent = mpValue.toFixed(1).padStart(5, ' ');
        
        // MP颜色警告
        const mpColor = mpValue > 50 ? '#4CAF50' : mpValue > 20 ? '#ffaa00' : '#ff4444';
        mpText.querySelector('.metric-number').style.color = mpColor;
    } else if (mpText) {
        mpText.querySelector('.metric-number').textContent = '--';
        mpText.querySelector('.metric-number').style.color = '#888';
    }
    
    if (expText && healthStats.exp_percent !== null && healthStats.exp_percent !== undefined) {
        const expValue = Math.round(healthStats.exp_percent * 10) / 10;
        expText.querySelector('.metric-number').textContent = expValue.toFixed(1).padStart(5, ' ');
        
        // EXP显示固定颜色
        expText.querySelector('.metric-number').style.color = '#ffaa00';
    } else if (expText) {
        expText.querySelector('.metric-number').textContent = '--';
        expText.querySelector('.metric-number').style.color = '#888';
    }
}

// 获取服务器状态
async function fetchServerStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        if (status.performance) {
            updateOptimizationStatus(status.performance.optimized_encoding);
            
            // 显示服务器端性能信息
            console.log('Server performance:', status.performance);
        }
        
        // 更新Bot状态
        if (status.bot_status) {
            updateBotStatus(status.bot_status, status.bot_state);
        }
        
        // 更新健康状态
        if (status.health_stats) {
            updateHealthStats(status.health_stats);
        }
    } catch (error) {
        console.error('Error fetching server status:', error);
    }
}

// 定期获取服务器状态 - 更频繁检查bot状态变化
setInterval(fetchServerStatus, 2000); // 每2秒检查一次

// 初始化时获取状态
fetchServerStatus();

// EXP图表相关功能
let expChart = null;
let currentExpTimeRange = 1; // 默认1小时

// 数据平滑算法 - 移动平均
function smoothData(data, windowSize = 3) {
    if (data.length < windowSize) return data;
    
    const smoothed = [];
    for (let i = 0; i < data.length; i++) {
        const start = Math.max(0, i - Math.floor(windowSize / 2));
        const end = Math.min(data.length, i + Math.floor(windowSize / 2) + 1);
        const window = data.slice(start, end);
        const avg = window.reduce((sum, val) => sum + val, 0) / window.length;
        smoothed.push(avg);
    }
    return smoothed;
}

// 检测升级并创建虚拟连接点
function detectLevelUps(snapshots) {
    const levelUps = [];
    
    for (let i = 1; i < snapshots.length; i++) {
        const prev = snapshots[i - 1];
        const curr = snapshots[i];
        
        // 检测升级：前一个快照EXP较高，当前快照EXP很低
        if (prev.curr_exp > 50 && curr.curr_exp < 50 && (prev.curr_exp - curr.curr_exp) > 50) {
            levelUps.push({
                prevSnapshot: prev,
                currSnapshot: curr,
                levelUpTime: prev.timestamp + (curr.timestamp - prev.timestamp) * 0.7 // 估算升级时间
            });
        }
    }
    
    return levelUps;
}

// 为升级创建虚拟数据点以保持线条连续性
function createLevelUpBridgePoints(snapshots, levelUps) {
    const bridgePoints = [];
    
    levelUps.forEach(levelUp => {
        const { prevSnapshot, currSnapshot, levelUpTime } = levelUp;
        
        // 创建升级前的100%虚拟点
        const bridgeTime = new Date(levelUpTime * 1000).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        bridgePoints.push({
            timestamp: levelUpTime,
            time: bridgeTime,
            curr_exp: 100, // 虚拟的100%点
            isLevelUpPoint: true,
            levelUpBefore: prevSnapshot,
            levelUpAfter: currSnapshot
        });
    });
    
    return bridgePoints;
}

// 数据拟合算法 - 分布增量到时间段
function fitIncrementalData(snapshots) {
    if (snapshots.length < 2) return [];
    
    const fitted = [];
    
    for (let i = 1; i < snapshots.length; i++) {
        const prev = snapshots[i - 1];
        const curr = snapshots[i];
        
        // 计算时间差（分钟）
        const timeDiffMinutes = (curr.timestamp - prev.timestamp) / 60;
        
        // 计算总的经验增长
        let expGain = curr.curr_exp - prev.curr_exp;
        if (expGain < -50) {
            // 处理升级情况
            expGain = (100 - prev.curr_exp) + curr.curr_exp;
        } else if (expGain < 0) {
            expGain = 0; // 忽略负增长
        }
        
        // 如果时间间隔大于1分钟，将增量均匀分布
        const intervalMinutes = Math.round(timeDiffMinutes);
        const expPerMinute = intervalMinutes > 0 ? expGain / intervalMinutes : expGain;
        
        // 为每分钟创建数据点
        for (let j = 0; j < Math.max(1, intervalMinutes); j++) {
            const minuteTimestamp = prev.timestamp + (j + 1) * 60;
            const minuteTime = new Date(minuteTimestamp * 1000).toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit'
            });
            
            fitted.push({
                timestamp: minuteTimestamp,
                time: minuteTime,
                exp_incremental: expPerMinute,
                original_gain: j === intervalMinutes - 1 ? expGain : 0, // 只在最后一分钟显示原始增量
                isLevelUpPeriod: expGain > 50 // 标记这是升级期间的增量
            });
        }
    }
    
    return fitted;
}

// 初始化EXP图表 - 复合图表双纵轴
function initExpChart() {
    const canvas = document.getElementById('exp-chart');
    if (!canvas) {
        console.error('Canvas element exp-chart not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('Cannot get 2D context from canvas');
        return;
    }
    
    console.log('Initializing EXP composite chart with dual y-axes...');
    
    try {
        expChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['等待数据'],
                datasets: [
                    {
                        label: 'EXP快照值(%)',
                        data: [0],
                        type: 'line',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y-left',
                        pointRadius: function(context) {
                            // 为升级点设置更大的半径
                            const index = context.dataIndex;
                            const chart = context.chart;
                            if (chart.levelUpMarkers && chart.levelUpMarkers[index]) {
                                return 6; // 升级点更大
                            }
                            return 3; // 普通点
                        },
                        pointBackgroundColor: function(context) {
                            // 为升级点设置特殊颜色
                            const index = context.dataIndex;
                            const chart = context.chart;
                            if (chart.levelUpMarkers && chart.levelUpMarkers[index]) {
                                return '#FFD700'; // 金色表示升级
                            }
                            return 'rgba(76, 175, 80, 1)'; // 普通绿色
                        },
                        pointBorderColor: function(context) {
                            const index = context.dataIndex;
                            const chart = context.chart;
                            if (chart.levelUpMarkers && chart.levelUpMarkers[index]) {
                                return '#FF8C00'; // 升级点边框
                            }
                            return 'rgba(76, 175, 80, 1)';
                        },
                        pointHoverRadius: 8,
                        tension: 0.1,
                        spanGaps: true  // 跳过null值连接线条
                    },
                    {
                        label: 'EXP增量(/分钟)',
                        data: [0],
                        type: 'bar',
                        backgroundColor: 'rgba(255, 170, 0, 0.7)',
                        borderColor: 'rgba(255, 170, 0, 1)',
                        borderWidth: 1,
                        yAxisID: 'y-right',
                        barThickness: 'flex',
                        maxBarThickness: 20
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#ccc',
                            maxTicksLimit: 15,
                            maxRotation: 45
                        },
                        grid: {
                            color: '#444'
                        }
                    },
                    'y-left': {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'EXP快照值(%)',
                            color: '#4CAF50'
                        },
                        ticks: {
                            color: '#4CAF50',
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        },
                        grid: {
                            color: '#444'
                        }
                    },
                    'y-right': {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'EXP增量(%/分钟)',
                            color: '#ffaa00'
                        },
                        ticks: {
                            color: '#ffaa00',
                            callback: function(value) {
                                return value.toFixed(2) + '%';
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                            color: '#666'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#ccc',
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#444',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const datasetLabel = context.dataset.label || '';
                                const value = context.raw;
                                const index = context.dataIndex;
                                const chart = context.chart;
                                
                                let label = '';
                                if (datasetLabel.includes('快照')) {
                                    label = `${datasetLabel}: ${value.toFixed(1)}%`;
                                    // 添加升级标记
                                    if (chart.levelUpMarkers && chart.levelUpMarkers[index]) {
                                        label += ' 🎉 升级!';
                                    }
                                } else {
                                    label = `${datasetLabel}: ${value.toFixed(3)}%`;
                                }
                                
                                return label;
                            },
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                const chart = context.chart;
                                
                                // 为升级点添加额外信息
                                if (chart.levelUpMarkers && chart.levelUpMarkers[index] && context.dataset.label.includes('快照')) {
                                    return ['', '🌟 恭喜升级!', '经验值重置为新等级0%'];
                                }
                                return null;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('EXP composite chart initialized successfully');
    } catch (error) {
        console.error('Error initializing EXP chart:', error);
    }
}

// 更改时间范围
function changeExpTimeRange(hours) {
    currentExpTimeRange = hours;
    
    // 更新按钮样式
    ['exp-chart-1h', 'exp-chart-3h', 'exp-chart-6h'].forEach(id => {
        const btn = document.getElementById(id);
        btn.style.backgroundColor = '#4CAF50';
    });
    
    document.getElementById(`exp-chart-${hours}h`).style.backgroundColor = '#ffaa00';
    
    // 更新图表数据
    updateExpChart();
}

// 获取原始快照数据用于计算
async function fetchRawSnapshotData() {
    try {
        const response = await fetch(`/api/exp/snapshots?hours=${currentExpTimeRange}`);
        const result = await response.json();
        return result.success ? (result.snapshots || []) : [];
    } catch (error) {
        console.error('Error fetching snapshot data:', error);
        return [];
    }
}

// 更新EXP复合图表数据
async function updateExpChart() {
    try {
        // 获取历史数据和原始快照数据
        const [historyResponse, rawSnapshots] = await Promise.all([
            fetch(`/api/exp/history?hours=${currentExpTimeRange}`),
            fetchRawSnapshotData()
        ]);
        
        const result = await historyResponse.json();
        
        console.log('EXP API Response:', result);
        console.log('Raw snapshots:', rawSnapshots);
        
        if (result.success) {
            const historyData = result.data || [];
            const stats = result.statistics || {};
            
            if (historyData.length === 0) {
                console.log('No EXP data available - showing empty chart');
                // 显示空图表提示
                expChart.data.labels = ['无数据'];
                expChart.data.datasets[0].data = [0]; // 快照数据
                expChart.data.datasets[1].data = [0]; // 增量数据
                expChart.update();
                
                // 清空统计信息
                updateExpStats({
                    total_exp_gain: 0,
                    avg_exp_per_minute: 0,
                    max_exp_per_minute: 0,
                    efficiency_percent: 0
                });
                return;
            }
            
            // 验证数据格式
            const sampleData = historyData[0];
            if (!sampleData.time || sampleData.exp_gain_per_minute === undefined) {
                console.error('Invalid data format:', sampleData);
                return;
            }
            
            // 检测升级情况
            const levelUps = detectLevelUps(historyData);
            console.log('Detected level ups:', levelUps.length);
            
            // 创建升级桥接点
            const bridgePoints = createLevelUpBridgePoints(historyData, levelUps);
            console.log('Bridge points created:', bridgePoints.length);
            
            // 合并快照数据和桥接点
            const enhancedSnapshots = [...historyData, ...bridgePoints].sort((a, b) => a.timestamp - b.timestamp);
            
            // 使用数据拟合算法计算增量数据
            const fittedData = fitIncrementalData(enhancedSnapshots);
            console.log('Fitted incremental data:', fittedData);
            
            // 合并时间轴 - 使用快照时间和拟合时间
            const allTimePoints = new Map(); // 时间 -> {snapshot: value, incremental: value, isLevelUp: boolean}
            
            // 添加快照时间点（包括桥接点）
            enhancedSnapshots.forEach(d => {
                if (!allTimePoints.has(d.time)) {
                    allTimePoints.set(d.time, {snapshot: null, incremental: null, isLevelUp: false});
                }
                // 只有在有有效数值时才设置，保持null让Chart.js跳过
                if (d.curr_exp !== null && d.curr_exp !== undefined) {
                    allTimePoints.get(d.time).snapshot = d.curr_exp;
                    allTimePoints.get(d.time).isLevelUp = d.isLevelUpPoint || false;
                }
            });
            
            // 添加拟合的增量时间点
            fittedData.forEach(d => {
                if (!allTimePoints.has(d.time)) {
                    allTimePoints.set(d.time, {snapshot: null, incremental: null, isLevelUp: false});
                }
                // 增量数据用0代替null（柱状图需要数值）
                allTimePoints.get(d.time).incremental = d.exp_incremental || 0;
                allTimePoints.get(d.time).isLevelUpPeriod = d.isLevelUpPeriod || false;
            });
            
            // 按时间排序并提取数据
            const sortedTimes = Array.from(allTimePoints.keys()).sort();
            const sortedLabels = sortedTimes;
            const sortedSnapshots = sortedTimes.map(time => allTimePoints.get(time).snapshot);
            const sortedIncrementals = sortedTimes.map(time => allTimePoints.get(time).incremental || 0);
            const levelUpMarkers = sortedTimes.map(time => allTimePoints.get(time).isLevelUp || false);
            
            // 统计升级次数
            const totalLevelUps = levelUpMarkers.filter(marker => marker).length;
            
            // 应用数据平滑到增量数据（可选）
            const smoothedIncrementals = smoothData(
                sortedIncrementals.map(v => v || 0),
                3
            );
            
            // 计算快照值的自适应Y轴范围
            const validSnapshots = sortedSnapshots.filter(v => v !== null);
            let snapshotMin = Math.min(...validSnapshots) - 1;
            let snapshotMax = Math.max(...validSnapshots) + 1;
            
            // 确保范围合理
            if (snapshotMax - snapshotMin < 5) {
                const center = (snapshotMax + snapshotMin) / 2;
                snapshotMin = center - 2.5;
                snapshotMax = center + 2.5;
            }
            
            // 调试输出数据结构
            console.log('EXP Chart Data:');
            console.log('Labels:', sortedLabels.length);
            console.log('Snapshots (with nulls):', sortedSnapshots.filter(v => v !== null).length, '/', sortedSnapshots.length);
            console.log('Incrementals:', sortedIncrementals.filter(v => v > 0).length, '/', sortedIncrementals.length);
            console.log('Level ups detected:', totalLevelUps);
            
            // 更新图表数据
            expChart.data.labels = sortedLabels;
            expChart.data.datasets[0].data = sortedSnapshots; // 保持null值让Chart.js跳过
            expChart.data.datasets[1].data = sortedIncrementals; // 已经处理过null值
            
            // 将升级标记数据附加到图表对象，供点样式函数使用
            expChart.levelUpMarkers = levelUpMarkers;
            
            // 更新左轴范围（快照值自适应）
            expChart.options.scales['y-left'].min = snapshotMin;
            expChart.options.scales['y-left'].max = snapshotMax;
            
            expChart.update();
            
            // 更新统计信息
            updateExpStats(stats);
            
            console.log(`Successfully updated composite chart with ${sortedLabels.length} time points`);
            console.log(`Snapshot range: ${snapshotMin.toFixed(1)}% - ${snapshotMax.toFixed(1)}%`);
        } else {
            console.error('API returned error:', result.error);
        }
    } catch (error) {
        console.error('Error updating EXP chart:', error);
    }
}

// 更新EXP统计信息显示
function updateExpStats(stats, totalLevelUps = 0) {
    const elements = {
        'exp-total-text': stats.total_exp_gain,
        'exp-avg-text': stats.avg_exp_per_minute,
        'exp-max-text': stats.max_exp_per_minute,
        'exp-level-ups': totalLevelUps,
        'exp-efficiency-text': stats.efficiency_percent
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            const numberSpan = element.querySelector('.metric-number');
            if (numberSpan) {
                if (id === 'exp-level-ups') {
                    // 升级次数显示为整数，无需padding
                    numberSpan.textContent = value.toString();
                } else {
                    numberSpan.textContent = value.toString().padStart(4, ' ');
                }
            }
        }
    });
}

// 更新EXP调试信息显示
function updateExpDebugInfo(debugInfo) {
    // 更新快照数量
    const snapshotsElement = document.getElementById('exp-debug-snapshots');
    if (snapshotsElement && debugInfo.snapshot_count !== undefined) {
        snapshotsElement.querySelector('.metric-number').textContent = debugInfo.snapshot_count.toString();
    }
    
    // 更新当前EXP
    const currentElement = document.getElementById('exp-debug-current');
    if (currentElement && debugInfo.current_exp !== null && debugInfo.current_exp !== undefined) {
        const expValue = Math.round(debugInfo.current_exp * 10) / 10;
        currentElement.querySelector('.metric-number').textContent = expValue.toString();
        currentElement.querySelector('.metric-number').style.color = '#ffaa00';
    } else if (currentElement) {
        currentElement.querySelector('.metric-number').textContent = '--';
        currentElement.querySelector('.metric-number').style.color = '#888';
    }
    
    // 更新上次快照时间
    const lastTimeElement = document.getElementById('exp-debug-last-time');
    if (lastTimeElement && debugInfo.last_snapshot_time) {
        const now = Date.now() / 1000;
        const elapsed = Math.round(now - debugInfo.last_snapshot_time);
        lastTimeElement.querySelector('.metric-number').textContent = elapsed + 's前';
        
        // 根据时间间隔设置颜色
        const color = elapsed < 90 ? '#4CAF50' : elapsed < 180 ? '#ffaa00' : '#ff4444';
        lastTimeElement.querySelector('.metric-number').style.color = color;
    } else if (lastTimeElement) {
        lastTimeElement.querySelector('.metric-number').textContent = '--';
        lastTimeElement.querySelector('.metric-number').style.color = '#888';
    }
}

// 检查是否有新快照并自动更新图表
let lastKnownSnapshotCount = 0;

function checkForNewSnapshots(debugInfo) {
    if (debugInfo.snapshot_count > lastKnownSnapshotCount) {
        console.log(`New snapshots detected: ${lastKnownSnapshotCount} → ${debugInfo.snapshot_count}`);
        lastKnownSnapshotCount = debugInfo.snapshot_count;
        
        // 延迟一点更新图表，确保数据已经同步
        setTimeout(() => {
            updateExpChart();
        }, 1000);
    }
}

// 重置EXP数据
async function resetExpData() {
    if (!confirm('确定要重置所有EXP追踪数据吗？这将清除所有历史记录。')) {
        return;
    }
    
    try {
        const response = await fetch('/api/exp/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert('EXP数据已重置');
            updateExpChart(); // 重新加载图表
        } else {
            alert('重置失败: ' + result.error);
        }
    } catch (error) {
        console.error('Error resetting EXP data:', error);
        alert('重置时出错: ' + error.message);
    }
}

// 调试EXP数据
async function debugExpData() {
    try {
        const response = await fetch('/api/exp/debug');
        const result = await response.json();
        
        if (result.success) {
            console.log('EXP Debug Info:', result.debug_info);
            alert(`EXP调试信息（查看控制台）:\n` +
                  `当前EXP: ${result.debug_info.current_exp_percent}%\n` +
                  `快照数量: ${result.debug_info.snapshot_count}\n` +
                  `最近快照: ${result.debug_info.recent_snapshots.length}个`);
        } else {
            alert('获取调试信息失败: ' + result.error);
        }
    } catch (error) {
        console.error('Error getting debug info:', error);
        alert('获取调试信息时出错: ' + error.message);
    }
}

// 生成测试数据
async function generateTestData() {
    try {
        const response = await fetch('/api/exp/generate_test_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        if (result.success) {
            alert(`测试数据生成成功！\n生成了 ${result.snapshots_count} 个快照`);
            updateExpChart(); // 刷新图表
        } else {
            alert('生成测试数据失败: ' + result.error);
        }
    } catch (error) {
        console.error('Error generating test data:', error);
        alert('生成测试数据时出错: ' + error.message);
    }
}

// 页面卸载时断开连接
window.onbeforeunload = function() {
    socket.disconnect();
};

// 初始化图表和定期更新
document.addEventListener('DOMContentLoaded', function() {
    initExpChart();
    updateExpChart();
    
    // 每30秒更新一次EXP图表
    setInterval(updateExpChart, 30000);
});