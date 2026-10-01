# -*- coding: utf-8 -*-
"""audio_postprocess.py — 配音后处理：去喷麦/去AI感/加呼吸感
用法：python audio_postprocess.py <in.mp3> <out.wav>
链路：highpass 去低频隆隆(喷麦) → deesser 去齿音 → 轻压缩 → 高频柔化(lowpass 14k) → 轻混响(房间感)
GPT-SoVITS 音轨同样过这条链（喷麦声主要在 200-800Hz 爆音，highpass+deesser 处理参考音频和输出都有效）。
"""
import sys, subprocess

FF = r"C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

CHAIN = (
    "highpass=f=110,"            # 去喷麦低频爆音
    "deesser,"                    # 去齿音
    "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,"  # 轻压缩提人味
    "lowpass=f=14000,"            # 柔化高频（电子感来源）
    "aecho=0.6:0.25:60:0.18"      # 极轻房间感（破塑料感）
)

def main():
    src, dst = sys.argv[1], sys.argv[2]
    cmd = [FF, "-y", "-i", src, "-af", CHAIN, "-ar", "44100", "-ac", "2", dst]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print("FAIL:", r.stderr[-400:]); sys.exit(1)
    print("OK ->", dst)

if __name__ == "__main__":
    main()
