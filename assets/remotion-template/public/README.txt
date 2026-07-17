把背景音乐文件放到这个目录，例如 public/bgm.mp3，
然后在场景/视频根部用：

  import { Bgm } from "../components/ui";
  <Bgm src="bgm.mp3" volume={0.35} />

注意：文件必须真实存在，否则渲染会报错。
模板默认场景不含 BGM，可开箱即渲染。
