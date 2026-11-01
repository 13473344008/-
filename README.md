# 星尘 · 单手粒子交互

基于原生 WebGL 和 MediaPipe 的浏览器粒子作品。四种形态持续自转、流动，支持单手换形与横向旋转；固定倾角和模型大小，带防抖与重新入镜衔接。

## 本地运行

需要 Node.js 和 Python 3。运行依赖已包含在仓库中，无需额外执行 `npm install`。

```sh
git clone https://github.com/13473344008/-.git gesture-stardust
cd gesture-stardust
npm start
```

打开 http://127.0.0.1:4173/ ，点击「开启手势」并允许摄像头。摄像头需要 localhost 或 HTTPS 环境，直接打开 HTML 文件不适用。

## 操作

| 手势 | 形态 |
| --- | --- |
| 握拳 | 星核 |
| 食指、中指比 V，无名指和小指收起；拇指自然放松 | 星环 |
| 五指自然张开 | 星团 |
| 只竖拇指 | 超新星 |

- 左右转掌控制横向旋转；上下倾斜、侧倾和前后移动不改变模型倾角或大小。
- 连续三帧识别到同一手势即可换形，随后有短暂防误触间隔。换形不依赖转向校准完成。
- 重新入镜会自动建立控制基准，无需对准目标；小幅手抖经过过滤。
- 不开启摄像头也可用鼠标左右拖动，数字 1–4 换形，R 重置视角。
- 设置中可选择香槟金或紫色、关闭手势换形、重置视角。

## 渲染与识别

桌面使用 96,000 个粒子，小屏使用 52,000 个粒子。星环球体和环带具有前后遮挡、投影、方向光及柔光；页面包含环境光晕与背景星点。所有形态共享每颗粒子的运动相位，使形态过渡保持连贯。

转向只取掌面法线的横向朝向，通过异常帧过滤、死区、速度限制和自适应平滑降低抖动。手势识别优先使用三维世界坐标；不可用时使用修正宽高比的二维关键点。自然张掌允许拇指放松、较短的小指及轻微弯曲，星环使用 V 手势，无需捏合。

形态属于艺术表达。真实识别效果会受光照、遮挡、摄像头和设备性能影响；自动测试不能代替真人体验。

## 检查

```sh
npm run check
```

包含语法检查与 56 项自动测试，覆盖四种手势、防误触、自然张掌、V 手势、转向防抖、重新入镜、透视和形态路径。

`tests/` 中还保留三种可复用的浏览器检查页。需要时临时复制到 `dist/`，检查结束删除临时副本：

```sh
cp tests/navigation-board.html dist/navigation-qa.html
cp tests/transition-board.html dist/transition-qa.html
cp tests/orbit-board.html dist/orbit-qa.html
```

分别访问 `/navigation-qa.html`、`/transition-qa.html`、`/orbit-qa.html`，可检查合成控制输入、12 个有向形态过渡和粒子随时间运动。临时检查页已加入忽略规则，不随当前版本上传。

## 文件结构

- `dist/`：可直接静态托管的网页、渲染代码与手势识别 Worker。
- `dist/vendor/`：手势模型、MediaPipe JavaScript/WASM 运行文件及第三方许可。
- `tests/`：自动测试与浏览器回归检查源文件。

## 依赖与隐私

使用 MediaPipe Tasks Vision 0.10.32 与官方 Hand Landmarker float16 v1。视频在本机 Worker 中处理，不上传、不录制。

SIMD 与非 SIMD WASM 文件分别服务于不同浏览器环境，均为运行资源，不是重复残留。第三方许可和来源说明保留在 `dist/vendor/LICENSE-2.0.txt` 与 `dist/vendor/MEDIAPIPE-README.md`。

- [MediaPipe Tasks Vision](https://www.npmjs.com/package/@mediapipe/tasks-vision/v/0.10.32)
- [Hand Landmarker 官方文档](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/web_js)
