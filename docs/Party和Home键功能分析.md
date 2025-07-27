# Party 和 Home 键功能分析

## 概述

在 MapleStory AutoLevelUp 项目中，`party` 和 `home` 键是两个重要的功能键，分别用于队伍管理和安全回城功能。本文档详细分析这两个键的具体用途、实现机制和使用场景。

## 1. Party 键 (默认: "p")

### 1.1 基本配置

```yaml
# config/config_default.yaml
key:
  party: "p"  # ⌨️ Party window shortcut
```

### 1.2 主要功能

#### 1.2.1 队伍窗口管理
**功能**: 打开/关闭队伍窗口
**实现位置**: `src/engine/MapleStoryAutoLevelUp.py` - `ensure_is_in_party()`

```python
def ensure_is_in_party(self):
    # 打开队伍窗口
    press_key(self.cfg["key"]["party"])
    
    # 等待队伍窗口显示
    time.sleep(0.5)
    
    # 更新图像帧
    self.img_frame = self.get_img_frame()
    
    # 查找"建立队伍"按钮
    loc_enable, score_enable, _ = find_pattern_sqdiff(
        self.img_frame, self.img_create_party_enable)
    
    # 如果找到建立队伍按钮，则点击建立队伍
    if score_enable < thres:
        click_in_game_window(self.capture.window_title,
            (loc_enable[0] + w // 2,
             loc_enable[1] + h // 2 + self.cfg['game_window']['title_bar_height']))
    
    # 关闭队伍窗口
    press_key(self.cfg["key"]["party"])
```

#### 1.2.2 队伍状态检测
**目的**: 确保角色处于队伍状态，以便进行位置识别
**检测机制**: 通过图像识别查找"建立队伍"按钮
- 如果找到按钮 → 角色未在队伍中 → 自动建立队伍
- 如果未找到按钮 → 角色已在队伍中 → 无需操作

#### 1.2.3 位置识别支持
**关键作用**: 为玩家位置识别提供红色血条
**原理**: 
- 只有队伍成员才会显示红色血条
- 红色血条用于 `get_player_location_by_party_red_bar()` 函数
- 当 `nametag.enable == False` 时，优先使用红色血条进行位置识别

### 1.3 使用场景

#### 1.3.1 脚本启动时
```python
# src/engine/MapleStoryAutoLevelUp.py - loop()
def loop(self):
    # 确保玩家在队伍中
    if not is_mac():
        activate_game_window(self.capture.window_title)
        time.sleep(0.3)
        self.ensure_is_in_party()  # 自动建立队伍
```

#### 1.3.2 换频道后
```python
# src/engine/MapleStoryAutoLevelUp.py - channel_change()
def channel_change(self):
    # ... 换频道流程 ...
    self.ensure_is_in_party()  # 换频道后重新建立队伍
```

### 1.4 相关配置

```yaml
# config/config_default.yaml
party_red_bar:
  # 队伍红色血条检测配置
  lower_red: [0, 60, 60]   # HSV, 较暗的红色
  upper_red: [0, 100, 100] # HSV, 较亮的红色
  offset: [20, 66]         # 从红色血条到角色中心的偏移
  create_party_button_cn_thres: 0.04   # 中文建立队伍按钮匹配阈值
  create_party_button_eng_thres: 0.04  # 英文建立队伍按钮匹配阈值
```

## 2. Home 键 (默认: "home")

### 2.1 基本配置

```yaml
# config/config_default.yaml
key:
  return_home: "home"  # 🔁 Key to use return home scroll.
```

### 2.2 主要功能

#### 2.2.1 安全回城机制
**功能**: 在危险情况下自动使用回城卷轴
**实现位置**: `src/engine/HealthMonitor.py` - 健康监控系统

```python
# src/engine/HealthMonitor.py
def get_hp_mp_exp_percent(self):
    # 检查是否需要回城
    if self.cfg["health_monitor"]["return_home_if_no_potion"]:
        if self.hp_percent >= hp_thres:
            self.t_hp_watch_dog = t_cur  # 重置看门狗
        else:
            # 如果看门狗超时，使用回城卷轴
            if t_cur - self.t_hp_watch_dog > watchdog_timeout:
                logger.warning(f"[Health Monitor] HP({self.hp_percent:.1f}%) < {hp_thres:.1f}% "
                               f"for {round(t_cur - self.t_hp_watch_dog, 2)} seconds.")
                logger.warning(f"[Health Monitor] Return home because potion is used up.")
                press_key(self.cfg["key"]["return_home"])  # 回城
                self.is_terminated = True  # 终止健康监控
                self.kb.is_terminated = True  # 终止自动机器人
```

#### 2.2.2 攻击超时保护
**功能**: 当长时间没有攻击时自动回城
**实现位置**: `src/engine/MapleStoryAutoLevelUp.py` - 攻击看门狗

```python
# src/engine/MapleStoryAutoLevelUp.py
def run_once(self):
    # 检查攻击超时
    if dt > self.cfg["watchdog"]["last_attack_timeout"]:
        cfg_action = self.cfg["watchdog"]["last_attack_timeout_action"]
        if cfg_action == "go_home":
            logger.info("[Attack Timeout] Return home!")
            press_key(self.cfg["key"]["return_home"])
            # 终止自动机器人
            self.is_terminated = True
            self.kb.is_terminated = True
```

### 2.3 使用场景

#### 2.3.1 血量不足保护
**触发条件**: 
- 血量低于设定阈值
- 持续一段时间未恢复
- 药水可能用完

**配置参数**:
```yaml
health_monitor:
  return_home_if_no_potion: False      # 是否启用无药水时回城
  return_home_watch_dog_timeout: 3     # 看门狗超时时间（秒）
```

#### 2.3.2 攻击异常保护
**触发条件**:
- 长时间没有攻击怪物
- 可能卡住或遇到异常情况

**配置参数**:
```yaml
watchdog:
  last_attack_timeout: 30              # 攻击超时时间（秒）
  last_attack_timeout_action: "go_home" # 超时动作：回城
```

### 2.4 安全机制

#### 2.4.1 多重保护
1. **血量监控**: 实时监控角色血量
2. **攻击监控**: 监控攻击频率
3. **看门狗机制**: 防止长时间异常状态

#### 2.4.2 优雅终止
- 回城后自动终止脚本
- 释放所有按键
- 清理资源

## 3. 键位绑定配置

### 3.1 UI界面配置
**位置**: Main标签页 → Key Bindings组
- **Party**: 队伍窗口快捷键设置
- **Home**: 回城键设置

### 3.2 配置验证
```python
# src/ui/ui.py
def update_cfg_from_main_ui(self):
    # 键位绑定配置
    self.cfg["key"]["party"] = self.party_key.get_key()
    self.cfg["key"]["return_home"] = self.return_home_key.get_key()
```

## 4. 技术特点

### 4.1 Party键特点
- **自动化**: 脚本启动时自动建立队伍
- **图像识别**: 通过按钮识别判断队伍状态
- **多语言支持**: 支持中英文界面
- **容错机制**: 队伍已存在时不会重复建立

### 4.2 Home键特点
- **安全优先**: 在危险情况下优先保护角色
- **多重触发**: 血量不足和攻击异常双重保护
- **自动终止**: 回城后自动停止脚本
- **可配置**: 支持启用/禁用和超时时间调整

## 5. 最佳实践

### 5.1 Party键使用建议
1. **确保按键正确**: 验证游戏中的队伍快捷键设置
2. **检查队伍状态**: 脚本启动前确认角色不在队伍中
3. **网络稳定**: 避免在网络不稳定时使用

### 5.2 Home键使用建议
1. **合理配置**: 根据角色强度调整血量阈值
2. **准备回城卷轴**: 确保背包中有足够的回城卷轴
3. **监控日志**: 关注回城触发的原因和频率
4. **测试验证**: 在安全环境下测试回城功能

## 6. 总结

`party` 和 `home` 键是项目中的两个重要安全机制：

- **Party键**: 确保位置识别正常工作，支持自动建立队伍
- **Home键**: 提供多重安全保护，在异常情况下自动回城

这两个键的设计体现了项目对安全性和稳定性的重视，通过自动化机制减少用户的手动干预，同时保护角色安全。 