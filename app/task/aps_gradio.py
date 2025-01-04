import os
import glob
import librosa
import numpy as np
import json
import time
import logging
from gradio_client import Client, file
from flask import current_app

# 配置日志
def setup_logger():
    logger = logging.getLogger('audio_processing')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

# 检查路径是否为 URL
def is_url(path):
    return isinstance(path, str) and (path.startswith("http://") or path.startswith("https://"))

# 处理路径：如果是 URL，使用 file()；如果是本地文件路径，直接传递
def prepare_paths(paths):
    return [file(path) if is_url(path) else path for path in paths]

# 保存已处理文件到JSON文件
def save_processed_files(processed_files, filename="processed_files.json"):
    with open(filename, 'w') as f:
        json.dump(list(processed_files), f)

# 从JSON文件加载已处理的文件
def load_processed_files(filename="processed_files.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(json.load(f))
    return set()

# 将文件列表分批，每批最多处理2个
def batch_process(paths, batch_size=2):
    for i in range(0, len(paths), batch_size):
        yield paths[i:i+batch_size]

# 批处理函数，处理多个文件，避免重复处理
def process_files(input_paths):
    start_time = time.time()
    
    # 从文件中加载已处理的文件列表
    processed_files = load_processed_files()

    # 过滤掉已经处理的文件
    files_to_process = [path for path in input_paths if path not in processed_files]

    if not files_to_process:
        logger.info("No new files to process.")
        return

    logger.info(f"Processing: {files_to_process}")
    
    # 1：处理去混响，按批次处理
    for batch in batch_process(files_to_process):
        paths = prepare_paths(batch)
        client = Client("http://127.0.0.1:15555/")
        result = client.predict(
            model_name="onnx_dereverb_By_FoxJoy",
            inp_root="",
            save_root_vocal="output/uvr5_opt",
            paths=[file(path) for path in paths],
            save_root_ins="output/uvr5_opt",
            agg=10,
            format0="wav",
            api_name="/uvr_convert"
        )
        logger.info(f"MDX-Net De-reverb result for {batch}: Success")
        
        # 2：获取去混响后的主 vocal 路径，并批量处理
        main_vocal_paths = []
        for input_path in batch:
            main_vocal_pattern = os.path.join('output', 'uvr5_opt', f'{os.path.basename(input_path)}*wav_main_vocal.wav')
            main_vocal_paths.extend(glob.glob(main_vocal_pattern))

        if main_vocal_paths:
            # 3：批量处理去回声
            for main_vocal_batch in batch_process(main_vocal_paths):
                paths = prepare_paths(main_vocal_batch)
                client = Client("http://127.0.0.1:15555/")
                result = client.predict(
                    model_name="VR-DeEchoAggressive",
                    inp_root="",
                    save_root_vocal="output/vc_uvr5_result",
                    paths=[file(path) for path in paths],
                    save_root_ins="output/vc_uvr5_result",
                    agg=10,
                    format0="wav",
                    api_name="/uvr_convert"
                )
                logger.info(f"DeEcho-Aggressive Echo removal result for {main_vocal_batch}: Success")

    # 更新已处理文件列表
    processed_files.update(files_to_process)

    # 保存已处理文件列表
    save_processed_files(processed_files)

    logger.info("Batch processing complete!, please check directory  `output/vc_uvr5_result`")
    
    # 记录总耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Total processing time: {elapsed_time:.2f} seconds")

# 批量获取本地音频文件（支持 .wav, .flac, .mp3, .m4a 格式）
def get_local_audio_files(input_folder):
    input_paths = []
    input_paths.extend(glob.glob(os.path.join(input_folder, "*.wav")))
    input_paths.extend(glob.glob(os.path.join(input_folder, "*.flac")))
    input_paths.extend(glob.glob(os.path.join(input_folder, "*.mp3")))
    input_paths.extend(glob.glob(os.path.join(input_folder, "*.m4a")))
    return input_paths

# 从 URL 或本地文件夹路径创建输入列表
def create_input_paths(input_folder, input_urls):
    local_paths = get_local_audio_files(input_folder)
    all_input_paths = local_paths + input_urls
    return all_input_paths

# URL 列表
input_urls = [
    #'https://raw.githubusercontent.com/zwong91/rt-audio/main/vc/liuyifei.wav',
]

def create_input_paths(input_folder):
    local_paths = get_local_audio_files(input_folder)
    return local_paths

# 批量处理函数，指定要处理的本地文件夹路径
input_folder = '/home/ubuntu/LiveAudio/vc'
#input_paths = create_input_paths(input_folder, input_urls)

def fix_audio(flask_app):
    """
    人声分离，去噪, 切片 定时任务
    :return:
    """
    with flask_app.app_context():
        # 执行批处理,每次获取最新的音频文件列表
        input_paths = get_local_audio_files(input_folder)
        #logger.info(f"batch inputs: {input_paths}")
        process_files(input_paths)
