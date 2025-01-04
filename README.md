From GPT-SoVITS
---

### Environments

- Python 3.10.13, PyTorch 2.1.1, CUDA 12.4(550)
- Python 3.10.13, PyTorch 2.1.1, macOS 14.4.1 (Apple silicon)

_Note: numba==0.56.4 requires py<3.11_

### Linux
```bash

rm /usr/bin/rclone
rm /usr/local/share/man/man1/rclone.1
wget https://downloads.rclone.org/v1.68.2/rclone-v1.68.2-linux-amd64.zip
apt update 
apt install zip unzip 
unzip rclone-v1.68.2-linux-amd64.zip
cp rclone-v1.68.2-linux-amd64/rclone  /usr/local/bin/
cp rclone-v1.68.2-linux-amd64/rclone /usr/bin/

mkdir -p ~/.config/rclone
cat << EOF > ~/.config/rclone/rclone.conf
[unc_cf]
type = s3
provider = Cloudflare
access_key_id = <TBD>
secret_access_key = <TBD>
endpoint = https://ec9b597fa02615ca6a0e62b7ff35d0cc.r2.cloudflarestorage.com
acl = private
EOF

#从s3 下载
rclone copy --no-check-certificate --progress --transfers=6  unc_cf:models/uvr5_weights.zip  ./

#上传到s3
rclone sync uvr5_weights.zip unc_cf:models/   --progress


# 安装 miniconda, PyTorch/CUDA 的 conda 环境
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash && source ~/miniconda3/bin/activate

conda create -n uvr5 python=3.10 -y
conda activate uvr5
bash install.sh
```

### macOS

**Note: The models trained with GPUs on Macs result in significantly lower quality compared to those trained on other devices, so we are temporarily using CPUs instead.**

1. Install Xcode command-line tools by running `xcode-select --install`.
2. Install FFmpeg by running `brew install ffmpeg`.
3. Install the program by running the following commands:

```bash
conda create -n uvr5 python=3.10
conda activate uvr5
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
 
```

### Install Manually

#### Install FFmpeg

##### Conda Users

```bash
conda install ffmpeg
```

##### Ubuntu/Debian Users

```bash
sudo apt install ffmpeg libsox-dev git git-lfs && sudo git lfs install
conda install -c conda-forge 'ffmpeg<7'
```

##### MacOS Users
```bash
brew install ffmpeg
```

#### Install Dependences

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

```

### Note on creating samples for quality voice cloning

The following post is a quote by user [Material1276 from reddit](https://www.reddit.com/r/Oobabooga/comments/1807tsl/comment/ka5l8w9/?share_id=_5hh4KJTXrEOSP0hR0hCK&utm_content=2&utm_medium=android_app&utm_name=androidcss&utm_source=share&utm_term=1)

> Some suggestions on making good samples
>
> Keep them about 7-9 seconds long. Longer isn't necessarily better.
>
> Make sure the audio is down sampled to a Mono, 22050Hz 16 Bit wav file. You will slow down processing by a large % and it seems cause poor quality results otherwise (based on a few tests). 24000Hz is the quality it outputs at anyway!
>
> Using the latest version of Audacity, select your clip and Tracks > Resample to 22050Hz, then Tracks > Mix > Stereo to Mono. and then File > Export Audio, saving it as a WAV of 22050Hz
>
> If you need to do any audio cleaning, do it before you compress it down to the above settings (Mono, 22050Hz, 16 Bit).
>
> Ensure the clip you use doesn't have background noises or music on e.g. lots of movies have quiet music when many of the actors are talking. Bad quality audio will have hiss that needs clearing up. The AI will pick this up, even if we don't, and to some degree, use it in the simulated voice to some extent, so clean audio is key!
>
> Try make your clip one of nice flowing speech, like the included example files. No big pauses, gaps or other sounds. Preferably one that the person you are trying to copy will show a little vocal range. Example files are in [here](https://github.com/oobabooga/text-generation-webui/tree/main/extensions/coqui_tts/voices)
>
> Make sure the clip doesn't start or end with breathy sounds (breathing in/out etc).
>
> Using AI generated audio clips may introduce unwanted sounds as its already a copy/simulation of a voice, though, this would need testing.

## Pretrained Models
**UVR5 模型(Vocals/Accompaniment Separation & Reverberation Removal, additionally), download models from [UVR5 Weights](https://huggingface.co/Delik/uvr5_weights) and place them in `/uvr5/uvr5_weights`.**

**https://ipv4.icanhazip.com**

1.Fill in the audio path

2.Slice the audio into small chunks

3.Denoise(optinal)

## Method for running from the command line
Use the command line to open the WebUI for UVR5
```
python uvr5/webui.py "<device>" <is_half> <webui_port_uvr5> <is_share>
```
<!-- If you can't open a browser, follow the format below for UVR processing,This is using mdxnet for audio processing
```
python mdxnet.py --model --input_root --output_vocal --output_ins --agg_level --format --device --is_half_precision
``` -->
This is how the audio segmentation of the dataset is done using the command line
```
python audio_slicer.py \
    --input_path "<path_to_original_audio_file_or_directory>" \
    --output_root "<directory_where_subdivided_audio_clips_will_be_saved>" \
    --threshold <volume_threshold> \
    --min_length <minimum_duration_of_each_subclip> \
    --min_interval <shortest_time_gap_between_adjacent_subclips> 
    --hop_size <step_size_for_computing_volume_curve>

### WebUI Tools
- [ultimatevocalremovergui](https://github.com/Anjok07/ultimatevocalremovergui)
- [audio-slicer](https://github.com/openvpi/audio-slicer)
- [SubFix](https://github.com/cronrpc/SubFix)
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [gradio](https://github.com/gradio-app/gradio)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)
