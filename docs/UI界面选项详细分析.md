# UI界面选项详细分析

## 概述

MapleStory AutoLevelUp 项目提供了一个功能丰富的图形用户界面，包含四个主要标签页：Main、Advanced Settings、Game Window Viz 和 Route Map Viz。本文档详细分析每个选项的含义和对应的源码实现。

## 1. Main 标签页

### 1.1 Bot Control 组 (🕹️ Bot Control)

#### 1.1.1 配置加载区域

**📂 Load Config 按钮**
- **功能**: 加载自定义配置文件
- **源码位置**: `src/ui/ui.py` - `create_control_gbox()`
- **对应函数**: `load_config()`
- **作用**: 允许用户选择并加载自定义的YAML配置文件，覆盖默认设置

**配置路径显示**
- **显示**: 当前加载的配置文件路径
- **默认**: "(No config loaded)"
- **存储**: 在用户主目录的 `.maplebot_ui_state.json` 中保存上次使用的配置路径

#### 1.1.2 控制按钮区域

**▶ Start (F1) 按钮**
- **功能**: 启动/暂停自动练级脚本
- **快捷键**: F1
- **源码位置**: `src/ui/ui.py` - `toggle_start_ui()`
- **对应函数**: 
  - `controller.start_bot()` - 启动脚本
  - `controller.pause_bot()` - 暂停脚本
- **状态变化**:
  - 启动时: 按钮变为 "⏸ Pause (F1)"，背景变绿
  - 暂停时: 按钮变为 "▶ Start (F1)"，背景恢复

**📸 Screenshot (F2) 按钮**
- **功能**: 截取游戏画面
- **快捷键**: F2
- **源码位置**: `src/ui/ui.py` - `toggle_screenshot_ui()`
- **对应函数**: `controller.take_screenshot()`
- **作用**: 保存当前游戏画面到 `screenshot/` 目录

**⏺ Record (F3) 按钮**
- **功能**: 开始/停止录制调试窗口
- **快捷键**: F3
- **源码位置**: `src/ui/ui.py` - `toggle_record_ui()`
- **对应函数**: 
  - `controller.start_recording()` - 开始录制
  - `controller.stop_recording()` - 停止录制
- **状态变化**:
  - 录制时: 按钮变为 "⏹ Stop (F3)"，背景变橙
  - 停止时: 按钮变为 "⏺ Record (F3)"，背景恢复

#### 1.1.3 Bot Mode 下拉框

**选项**:
- `normal`: 正常模式 - 完整的自动练级功能
- `aux`: 辅助模式 - 仅执行辅助功能（如自动喝药、buff）
- `patrol`: 巡逻模式 - 仅在地图上巡逻，不攻击怪物

**源码位置**: `src/ui/ui.py` - `create_control_gbox()`
**对应配置**: `config/config_default.yaml` - `bot.mode`

### 1.2 Attack Settings 组 (⚔️ Attack Settings)

#### 1.2.1 Attack Mode 下拉框

**选项**:
- `Basic`: 基础攻击模式 - 使用方向性攻击技能
- `AOE Skill`: 范围攻击模式 - 使用AOE技能

**源码位置**: `src/ui/ui.py` - `create_attack_gbox()`
**对应函数**: `update_atk_config_trigger_by_drop_list()`

#### 1.2.2 攻击范围设置

**Range X**: 水平攻击范围（像素）
- **默认值**: 根据攻击模式自动设置
- **验证**: 0-9999 整数
- **对应配置**: `directional_attack.range_x` 或 `aoe_skill.range_x`

**Range Y**: 垂直攻击范围（像素）
- **默认值**: 根据攻击模式自动设置
- **验证**: 0-9999 整数
- **对应配置**: `directional_attack.range_y` 或 `aoe_skill.range_y`

**Cooldown (s)**: 攻击冷却时间（秒）
- **默认值**: 根据攻击模式自动设置
- **验证**: 0-9999 浮点数
- **对应配置**: `directional_attack.cooldown` 或 `aoe_skill.cooldown`

### 1.3 Key Bindings 组 (🎮 Key Bindings)

#### 1.3.1 基础按键设置

**Basic Attack**: 基础攻击键
- **对应配置**: `key.directional_attack`
- **默认值**: "w"

**AOE Skill**: 范围技能键
- **对应配置**: `key.aoe_skill`
- **默认值**: "q"

**Teleport**: 传送技能键
- **对应配置**: `key.teleport`
- **默认值**: "e"
- **说明**: 设置为空字符串可禁用传送功能

#### 1.3.2 移动按键设置

**Jump**: 跳跃键
- **对应配置**: `key.jump`
- **默认值**: "space"

**Home**: 回城键
- **对应配置**: `key.return_home`
- **默认值**: "home"

#### 1.3.3 功能按键设置

**Party**: 队伍窗口键
- **对应配置**: `key.party`
- **默认值**: "p"

**源码位置**: `src/ui/ui.py` - `create_key_binding_gbox()`
**输入控件**: `SingleKeyEdit` - 支持单键输入验证

### 1.4 Pet Skills 组 (❤️ Pet Skills)

#### 1.4.1 Auto Add HP 设置

**Auto Add HP 复选框**
- **功能**: 启用自动喝HP药水
- **对应配置**: `health_monitor.add_hp_percent > 0`

**When HP is below**: HP百分比阈值
- **默认值**: 50
- **验证**: 0-100 整数
- **对应配置**: `health_monitor.add_hp_percent`

**press [KEY] key**: HP药水按键
- **对应配置**: `key.add_hp`
- **默认值**: "1"

#### 1.4.2 Auto Add MP 设置

**Auto Add MP 复选框**
- **功能**: 启用自动喝MP药水
- **对应配置**: `health_monitor.add_mp_percent > 0`

**When MP is below**: MP百分比阈值
- **默认值**: 50
- **验证**: 0-100 整数
- **对应配置**: `health_monitor.add_mp_percent`

**press [KEY] key**: MP药水按键
- **对应配置**: `key.add_mp`
- **默认值**: "2"

#### 1.4.3 Auto Buff 设置

**Auto Buff 复选框**
- **功能**: 启用自动施放buff技能
- **对应配置**: `buff_skill.keys` 不为空

**动态Buff行**
- **功能**: 可添加多个buff技能
- **结构**: [按键] [冷却时间(秒)]
- **对应配置**: `buff_skill.keys` 和 `buff_skill.cooldown`

**+ Add Buff Key 按钮**
- **功能**: 添加新的buff技能行
- **源码位置**: `src/ui/ui.py` - `add_buff_row()`

**源码位置**: `src/ui/ui.py` - `create_pet_skill_gbox()`

### 1.5 Map 组 (🗺️ Map)

#### 1.5.1 地图选择列表

**地图列表**
- **数据源**: `minimaps/` 目录
- **显示格式**: "英文名 (中文名)"
- **对应配置**: `bot.map`
- **源码位置**: `src/ui/ui.py` - `create_map_selection_gbox()`

**地图信息显示**
- **显示**: 选中地图的路径信息
- **格式**: "Selected map: minimaps/地图名"

**源码位置**: `src/ui/ui.py` - `on_map_selected()`

### 1.6 Log 组 (📜 Log)

#### 1.6.1 日志输出窗口

**日志显示区域**
- **功能**: 实时显示脚本运行日志
- **只读**: 用户无法编辑
- **最大高度**: 150像素
- **格式**: `[时间] 级别: 消息`

**日志处理器**
- **类型**: `QtLogHandler`
- **源码位置**: `src/ui/ui.py` - `create_log_gbox()`
- **信号连接**: `log_signal.connect(self.append_log)`

## 2. Advanced Settings 标签页

### 2.1 标签页结构

**布局**: 双列布局，左右各显示一半的配置组
**滚动**: 支持垂直滚动，适合大量设置项
**隐藏配置**: `key` 和 `bot` 配置组在高级设置中隐藏

### 2.2 配置组生成

**自动生成**: 根据 `config_default.yaml` 自动生成配置组
**源码位置**: `src/utils/ui.py` - `create_advance_setting_gbox()`

#### 2.2.1 配置项类型

**布尔值 (CheckBox)**
- **控件**: QCheckBox
- **示例**: 各种启用/禁用选项
- **更新**: 实时更新配置

**数值 (LineEdit)**
- **控件**: QLineEdit
- **验证器**: QIntValidator 或 QDoubleValidator
- **示例**: 范围、冷却时间、阈值等

**列表/元组 (多个LineEdit)**
- **控件**: 多个QLineEdit水平排列
- **示例**: 坐标、颜色值等
- **更新**: 所有输入框变化时更新

**字符串 (LineEdit 或 ComboBox)**
- **控件**: QLineEdit 或 QComboBox
- **下拉框**: 当注释中包含 "Options:" 时自动生成
- **示例**: 语言选择、模式选择等

### 2.3 配置组示例

#### 2.3.1 system 组
- **fps_limit_window_capturor**: 窗口截图FPS限制
- **fps_limit_keyboard_controller**: 键盘控制器FPS限制
- **fps_limit_auto_dice_roller**: 自动掷骰FPS限制
- **language**: 语言选择 (Options: "eng", "cn")

#### 2.3.2 game_window 组
- **title**: 游戏窗口标题关键字
- **title_bar_height**: 标题栏高度
- **size**: 游戏窗口尺寸 [宽度, 高度]

#### 2.3.3 monster_detect 组
- **mode**: 怪物检测模式 (Options: "color", "grayscale", "contour_only", "template_free")
- **diff_thres**: 模板匹配阈值
- **search_box_margin**: 搜索框边距
- **contour_blur**: 轮廓模糊核大小
- **with_enemy_hp_bar**: 是否使用敌人血条检测

#### 2.3.4 nametag 组
- **enable**: 是否启用名字标签检测
- **name**: 名字标签模板文件名
- **mode**: 检测模式 (Options: "grayscale", "white_mask", "histogram_eq")
- **offset**: 名字标签到角色中心的偏移 [x, y]
- **diff_thres**: 匹配阈值

#### 2.3.5 party_red_bar 组
- **lower_red**: 红色血条HSV下限 [H, S, V]
- **upper_red**: 红色血条HSV上限 [H, S, V]
- **offset**: 血条到角色中心的偏移 [x, y]

#### 2.3.6 minimap 组
- **player_color**: 玩家在小地图上的颜色 [B, G, R]
- **other_player_color**: 其他玩家在小地图上的颜色 [B, G, R]
- **debug_window_upscale**: 调试窗口放大倍数
- **offset**: 小地图偏移 [x, y]

#### 2.3.7 rune_detect 组
- **box_width**: 符文检测框宽度
- **box_height**: 符文检测框高度
- **diff_thres**: 符文匹配阈值

#### 2.3.8 rune_solver 组
- **arrow_box_size**: 箭头框大小
- **arrow_box_interval**: 箭头框间隔
- **arrow_box_coord**: 第一个箭头框坐标 [x, y]
- **arrow_box_diff_thres**: 箭头框匹配阈值

#### 2.3.9 channel_change 组
- **enable**: 是否启用自动换频道
- **mode**: 换频道模式 (Options: "true", "pixel")
- **other_player_move_thres**: 其他玩家移动阈值

#### 2.3.10 scheduled_channel_switching 组
- **enable**: 是否启用定时换频道
- **interval_seconds**: 换频道间隔（秒）

## 3. Game Window Viz 标签页

### 3.1 标签页功能

**功能**: 实时显示游戏窗口的调试可视化
**窗口大小**: 
- Windows: 1280x650
- macOS: 850x430（适配MacBook屏幕）

### 3.2 显示内容

**调试画布**
- **控件**: QLabel 作为画布
- **背景**: 黑色背景，白色文字
- **源码位置**: `src/ui/ui.py` - `setup_game_window_viz_tab()`

**显示内容**:
- 游戏窗口截图
- 检测框和标记
- 玩家位置标记
- 怪物检测框
- 符文检测区域
- 各种调试信息

### 3.3 信号连接

**信号**: `debug_image_signal`
**连接**: `ui.update_debug_canvas()`
**源码位置**: `src/ui/AutoBotController.py` - `update_signal()`

### 3.4 启用/禁用

**启用**: 切换到该标签页时自动启用
**禁用**: 切换到其他标签页时自动禁用
**源码位置**: `src/ui/ui.py` - `on_tab_changed()`

## 4. Route Map Viz 标签页

### 4.1 标签页功能

**功能**: 实时显示路线地图的可视化
**窗口大小**: 
- Windows: 800x800
- macOS: 400x400

### 4.2 显示内容

**路线地图画布**
- **控件**: QLabel 作为画布
- **背景**: 黑色背景，白色文字
- **源码位置**: `src/ui/ui.py` - `setup_route_map_viz_tab()`

**显示内容**:
- 当前地图的完整路线图
- 玩家当前位置（黄色圆点）
- 其他玩家位置（红色圆点）
- 小地图区域（黄色矩形）
- 路径颜色编码
- 探索过的区域

### 4.3 信号连接

**信号**: `route_map_viz_signal`
**连接**: `ui.update_route_map_canvas()`
**源码位置**: `src/ui/AutoBotController.py` - `update_signal()`

### 4.4 图像处理

**缩放**: 保持宽高比缩放
**转换**: BGR到QImage格式转换
**源码位置**: `src/ui/ui.py` - `update_route_map_canvas()`

## 5. 标签页切换逻辑

### 5.1 切换处理

**源码位置**: `src/ui/ui.py` - `on_tab_changed()`

#### 5.1.1 Game Window Viz / Route Map Viz
```python
if tab_name in ["Game Window Viz", "Route Map Viz"]:
    self.controller.enable_bot_viz()  # 启用可视化
```

#### 5.1.2 Main
```python
elif tab_name == "Main":
    self.controller.disable_bot_viz()  # 禁用可视化
    self.apply_config_to_ui()  # 应用配置到UI
```

#### 5.1.3 Advanced Settings
```python
elif tab_name == "Advanced Settings":
    self.controller.disable_bot_viz()  # 禁用可视化
    self.update_cfg_from_main_ui()  # 从主UI更新配置
    self.apply_config_to_ui()  # 应用配置到UI
```

### 5.2 窗口大小调整

**动态调整**: 根据标签页自动调整窗口大小
**配置**: `TAB_WINDOW_SIZE` 字典
**源码位置**: `src/ui/ui.py` - `on_tab_changed()`

## 6. 配置管理

### 6.1 配置加载

**基础配置**: `config/config_default.yaml`
**平台配置**: `config/config_macOS.yaml`（仅macOS）
**自定义配置**: 用户选择的配置文件

### 6.2 配置应用

**主UI到配置**: `update_cfg_from_main_ui()`
**配置到主UI**: `apply_config_to_ui()`
**高级设置**: `update_advance_setting_ui_from_cfg()`

### 6.3 配置保存

**临时配置**: `config/.config_tmp.yaml`
**UI状态**: `~/.maplebot_ui_state.json`

## 7. 快捷键支持

### 7.1 功能键

**F1**: 启动/暂停脚本
**F2**: 截图
**F3**: 开始/停止录制
**F12**: 关闭程序

### 7.2 键盘监听

**监听器**: `KeyBoardListener`
**注册**: `register_func_key_handler()`
**源码位置**: `src/ui/AutoBotController.py` - `update_signal()`

## 8. 错误处理

### 8.1 输入验证

**数值验证**: `validate_numerical_input()`
**错误标签**: `create_error_label()`
**实时验证**: 输入框失去焦点时验证

### 8.2 配置验证

**加载错误**: 显示错误信息
**验证失败**: 阻止启动脚本
**优雅降级**: 使用默认值

## 9. 技术特点

### 9.1 模块化设计

- **控制器模式**: UI与引擎分离
- **信号槽机制**: 异步通信
- **配置驱动**: 基于YAML的配置系统

### 9.2 用户体验

- **实时反馈**: 即时显示状态变化
- **可视化调试**: 直观的调试信息
- **配置持久化**: 记住用户设置
- **多语言支持**: 中英文界面

### 9.3 性能优化

- **按需加载**: 只在需要时启用可视化
- **窗口大小优化**: 不同平台适配
- **滚动支持**: 处理大量配置项

这个UI设计体现了现代桌面应用的最佳实践，提供了丰富的功能和良好的用户体验。 