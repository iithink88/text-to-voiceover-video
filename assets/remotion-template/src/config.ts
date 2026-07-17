// 自动生成，请勿手动修改（由生成脚本 text-to-voiceover-video/scripts/generate_video.py 写入）。
// 如需手动调整，改这里即可，然后重新渲染。

/** 投放平台比例：9:16(抖音) / 16:9(YouTube) / 3:4(小红书) */
export const ASPECT = "9:16";

/** 画布宽高（像素） */
export const WIDTH = 1080;
export const HEIGHT = 1920;

/** 帧率 */
export const FPS = 30;

/** 每个场景的默认时长（秒）。当 SCENE_DURATIONS 为空时，所有屏都用这个值。 */
export const SCENE_SECONDS = 5;

/** 逐屏时长（秒）数组：音画同步时由生成脚本按比例写入（每屏字数越多停留越久）。
 *  为空 [] 时回退到 SCENE_SECONDS。长度可与场景数不一致，缺的屏用 SCENE_SECONDS。 */
export const SCENE_DURATIONS: number[] = [];

/** 视觉风格：dark(科技暗色) / light(简约亮色) / brand(品牌蓝) */
export const STYLE = "dark";
