# CP16: Visual Baseline Style Variants

## Overview

CP16 introduces 3 new visual templates (themes) for the Web Studio to enable A/B comparison of different news video visual styles. This establishes a visual baseline for future iterations.

## New Visual Templates

### 1. research_desk_v2 (AI 研究室 v2)

**定位:** 深夜研究室 / AI 前沿解读

**视觉特点:**
- 深色背景 (#0a0f1a)
- 蓝色调主题 (#4a9eff)
- 科技感强，适合 AI 技术新闻

**布局:**
- 顶部标题自适应换行（最多3行）
- 节点使用 research_card 样式
- 对话卡片位于 desk_cards 位置

**适合场景:**
- AI 技术新闻
- 模型发布
- 研究动态
- 学术类新闻解读

### 2. news_card_v1 (新闻大卡片)

**定位:** 新闻资讯卡片风格

**视觉特点:**
- 深色背景 (#1a1a2e)
- 橙色调主题 (#ff6b35)
- 中央大标题 + 三张关键点卡片

**布局:**
- 中央大新闻标题
- 节点使用 modern_panel 样式
- 对话卡片位于 side 位置

**适合场景:**
- 热点新闻
- 公司发布
- 监管新闻
- 突发新闻

### 3. causal_map_v1 (因果链地图)

**定位:** 因果链动画图风格

**视觉特点:**
- 深色背景 (#0d1b2a) + 网格
- 青色主题 (#00d4ff)
- 圆形节点（区别于其他模板的矩形节点）

**布局:**
- 圆形节点显示因果链
- 边（edges）作为主视觉连接
- 适合展示事件因果关系

**适合场景:**
- 解释性新闻
- 原因分析
- 影响评估
- "为什么发生、导致什么影响"类新闻

## Current Visual Defects (Before CP17)

1. **标题溢出**: 长标题需要自适应换行，已实现
2. **副标题截断**: 副标题限制2行，已实现
3. **信息密度低**: 单卡片布局已优化为多卡片
4. **新闻包装感不足**: 新模板增加了视觉层次
5. **缺少分区**: 新模板支持节点+边+callout的组合

## Next Steps (CP17)

1. **Remotion 集成**: 将 HTML 动画转换为专业视频
2. **数字人**: 添加主播/专家形象
3. **复杂导出**: 支持更高质量的 MP4 导出
4. **动效增强**: 节点进入动画、边动画、callout 动画

## User Acceptance Criteria

用户验收标准：

1. **是否像新闻视频?**
   - 标题清晰可见
   - 有主持人/专家对话感
   - 画面有层次感

2. **标题是否清楚?**
   - 长标题能正常换行
   - 不溢出画布
   - 字号适中可读

3. **信息是否足够?**
   - 节点展示关键信息
   - callout 补充说明
   - 对话字幕清晰

4. **节奏是否能看懂?**
   - beat 按时间顺序展开
   - 当前节点高亮
   - 淡入淡出平滑

5. **哪个模板最接近目标?**
   - research_desk_v2: 科技/AI 新闻
   - news_card_v1: 热点/突发新闻
   - causal_map_v1: 解释性/因果分析新闻

## API Changes

### /api/themes Response

```json
{
  "default_theme": "chalkboard",
  "themes": [
    {"id": "causal_map_v1", "name": "因果链地图"},
    {"id": "chalkboard", "name": "绿色黑板"},
    {"id": "news_card_v1", "name": "新闻大卡片"},
    {"id": "notebook", "name": "手写笔记"},
    {"id": "podcast", "name": "双人播客"},
    {"id": "research_desk", "name": "深夜研究室"},
    {"id": "research_desk_v2", "name": "AI 研究室 v2"}
  ]
}
```

## Files Changed

- `config/themes.yaml`: Added 3 new themes
- `src/theme.py`: Added new layout variants
- `renderer/template.html`: Enhanced text fitting and animations
- `src/server.py`: Updated /api/themes to return theme objects
- `web/app.js`: Updated theme selector and recommended hint
- `docs/CP16_VISUAL_BASELINE.md`: This document

## Testing

See E2E validation commands in the task description. Run with:

1. `theme=research_desk_v2`
2. `theme=news_card_v1`
3. `theme=causal_map_v1`

Each should produce a working animation.html with distinct visual appearance.
