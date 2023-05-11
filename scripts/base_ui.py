import sys, os
basedirs = [os.getcwd()]

for basedir in basedirs:
    paths_to_ensure = [
        basedir,
        basedir + '/extensions/sd-cn-animation/scripts',
        basedir + '/extensions/SD-CN-Animation/scripts'
        ]

    for scripts_path_fix in paths_to_ensure:
        if not scripts_path_fix in sys.path:
            sys.path.extend([scripts_path_fix])

import gradio as gr
import modules
from types import SimpleNamespace

from modules import script_callbacks, shared
from modules.shared import cmd_opts, opts
from webui import wrap_gradio_gpu_call

from modules.ui_components import ToolButton, FormRow, FormGroup
from modules.ui import create_override_settings_dropdown
import modules.scripts as scripts

from modules.sd_samplers import samplers_for_img2img
from modules.ui import setup_progressbar, create_sampler_and_steps_selection, ordered_ui_categories, create_output_panel

from core import vid2vid, txt2vid, utils
import traceback

def V2VArgs():
    seed = -1
    width = 1024
    height = 576
    cfg_scale = 5.5
    steps = 15
    prompt = ""
    n_prompt = "text, letters, logo, brand, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"
    processing_strength = 0.85
    fix_frame_strength = 0.15
    return locals()

def T2VArgs():
    seed = -1
    width = 768
    height = 512
    cfg_scale = 5.5
    steps = 15
    prompt = ""
    n_prompt = "text, letters, logo, brand, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"
    processing_strength = 0.85
    fix_frame_strength = 0.35
    return locals()

def setup_common_values(mode, d):
    with gr.Row():
        width = gr.Slider(label='Width', minimum=64, maximum=2048, step=64, value=d.width, interactive=True)
        height = gr.Slider(label='Height', minimum=64, maximum=2048, step=64, value=d.height, interactive=True)
    with gr.Row(elem_id=f'{mode}_prompt_toprow'):
        prompt = gr.Textbox(label='Prompt', lines=3, interactive=True, elem_id=f"{mode}_prompt", placeholder="Enter your prompt here...")
    with gr.Row(elem_id=f'{mode}_n_prompt_toprow'):
        n_prompt = gr.Textbox(label='Negative prompt', lines=3, interactive=True, elem_id=f"{mode}_n_prompt", value=d.n_prompt)
    with gr.Row():
        cfg_scale = gr.Slider(label='CFG scale', minimum=1, maximum=100, step=1, value=d.cfg_scale, interactive=True)
    with gr.Row():
        seed = gr.Number(label='Seed (this parameter controls how the first frame looks like and the color distribution of the consecutive frames as they are dependent on the first one)', value = d.seed, Interactive = True, precision=0)
    with gr.Row():
        processing_strength = gr.Slider(label="Processing strength", value=d.processing_strength, minimum=0, maximum=1, step=0.05, interactive=True)
        fix_frame_strength = gr.Slider(label="Fix frame strength", value=d.fix_frame_strength, minimum=0, maximum=1, step=0.05, interactive=True)
    with gr.Row():
        sampler_index = gr.Dropdown(label='Sampling method', elem_id=f"{mode}_sampling", choices=[x.name for x in samplers_for_img2img], value=samplers_for_img2img[0].name, type="index", interactive=True)
        steps = gr.Slider(label="Sampling steps", minimum=1, maximum=150, step=1, elem_id=f"{mode}_steps", value=d.steps, interactive=True)

    return width, height, prompt, n_prompt, cfg_scale, seed, processing_strength, fix_frame_strength, sampler_index, steps

def inputs_ui():
    v2v_args = SimpleNamespace(**V2VArgs())
    t2v_args = SimpleNamespace(**T2VArgs())
    with gr.Tabs():
        sdcn_process_mode = gr.State(value='vid2vid')

        with gr.Tab('vid2vid') as tab_vid2vid:
            with gr.Row():
                gr.HTML('Put your video here')
            with gr.Row():
                v2v_file = gr.File(label="Input video", interactive=True, file_count="single", file_types=["video"], elem_id="vid_to_vid_chosen_file")

            v2v_width, v2v_height, v2v_prompt, v2v_n_prompt, v2v_cfg_scale, v2v_seed, v2v_processing_strength, v2v_fix_frame_strength, v2v_sampler_index, v2v_steps = setup_common_values('vid2vid', v2v_args)

            with FormRow(elem_id="vid2vid_override_settings_row") as row:
                v2v_override_settings = create_override_settings_dropdown("vid2vid", row)

            with FormGroup(elem_id=f"script_container"):
                v2v_custom_inputs = scripts.scripts_img2img.setup_ui()
            
        with gr.Tab('txt2vid') as tab_txt2vid:
            t2v_width, t2v_height, t2v_prompt, t2v_n_prompt, t2v_cfg_scale, t2v_seed, t2v_processing_strength, t2v_fix_frame_strength, t2v_sampler_index, t2v_steps = setup_common_values('txt2vid', t2v_args)
            with gr.Row():
                t2v_length = gr.Slider(label='Length (in frames)', minimum=10, maximum=2048, step=10, value=40, interactive=True)
                t2v_fps = gr.Slider(label='Video FPS', minimum=4, maximum=64, step=4, value=12, interactive=True)
        
    
    tab_vid2vid.select(fn=lambda: 'vid2vid', inputs=[], outputs=[sdcn_process_mode])
    tab_txt2vid.select(fn=lambda: 'txt2vid', inputs=[], outputs=[sdcn_process_mode])
         
    return locals()

def process(*args):
    msg = 'Done'
    try:    
        if args[0] == 'vid2vid':
            yield from vid2vid.start_process(*args)
        elif args[0] == 'txt2vid':
            yield from txt2vid.start_process(*args)
        else:
            msg = f"Unsupported processing mode: '{args[0]}'"
            raise Exception(msg)
    except Exception as error:
        # handle the exception
        msg = f"An exception occurred while trying to process the frame: {error}"
        print(msg)
        traceback.print_exc()
    
    yield msg, gr.Image.update(), gr.Image.update(), gr.Image.update(), gr.Image.update(), gr.Video.update(), gr.Button.update(interactive=True), gr.Button.update(interactive=False)

def stop_process(*args):
    utils.shared.is_interrupted = True
    return gr.Button.update(interactive=False)

def on_ui_tabs():
    modules.scripts.scripts_current = modules.scripts.scripts_img2img
    modules.scripts.scripts_img2img.initialize_scripts(is_img2img=True)

    with gr.Blocks(analytics_enabled=False) as sdcnanim_interface:
        components = {}
        
        #dv = SimpleNamespace(**T2VOutputArgs())
        with gr.Row(elem_id='sdcn-core').style(equal_height=False, variant='compact'):
            with gr.Column(scale=1, variant='panel'):
                with gr.Tabs():
                    components = inputs_ui()
    
            with gr.Column(scale=1, variant='compact'):
                with gr.Row(variant='compact'):
                    run_button = gr.Button('Generate', elem_id=f"sdcn_anim_generate", variant='primary')
                    stop_button = gr.Button('Interrupt', elem_id=f"sdcn_anim_interrupt", variant='primary', interactive=False)

                with gr.Column(variant="panel"):
                    sp_progress = gr.HTML(elem_id="sp_progress", value="")
                    sp_progress.update()
                    #sp_outcome = gr.HTML(elem_id="sp_error", value="")
                    #sp_progressbar = gr.HTML(elem_id="sp_progressbar")
                    #setup_progressbar(sp_progressbar, sp_preview, 'sp', textinfo=sp_progress)
                    
                    with gr.Row(variant='compact'):
                        img_preview_curr_frame = gr.Image(label='Current frame', elem_id=f"img_preview_curr_frame", type='pil').style(height=240)
                        img_preview_curr_occl = gr.Image(label='Current occlusion', elem_id=f"img_preview_curr_occl", type='pil').style(height=240)
                    with gr.Row(variant='compact'):
                        img_preview_prev_warp = gr.Image(label='Previous frame warped', elem_id=f"img_preview_curr_frame", type='pil').style(height=240)
                        img_preview_processed = gr.Image(label='Processed', elem_id=f"img_preview_processed", type='pil').style(height=240)
                    
                    # html_log = gr.HTML(elem_id=f'html_log_vid2vid')
                    video_preview = gr.Video(interactive=False)
                
                with gr.Row(variant='compact'):
                    dummy_component = gr.Label(visible=False)

            # Define parameters for the action methods.
            method_inputs = [components[name] for name in utils.get_component_names()] + components['v2v_custom_inputs']

            method_outputs = [
                sp_progress,
                img_preview_curr_frame,
                img_preview_curr_occl,
                img_preview_prev_warp,
                img_preview_processed,
                video_preview,
                run_button,
                stop_button,
            ]

            run_button.click(
                fn=process, #wrap_gradio_gpu_call(start_process, extra_outputs=[None, '', '']), 
                inputs=method_inputs,
                outputs=method_outputs,
                show_progress=True,
            )

            stop_button.click(
                fn=stop_process,
                outputs=[stop_button],
                show_progress=False
            )

        modules.scripts.scripts_current = None

        # define queue - required for generators
        sdcnanim_interface.queue(concurrency_count=1)
    return [(sdcnanim_interface, "SD-CN-Animation", "sd_cn_animation_interface")]


script_callbacks.on_ui_tabs(on_ui_tabs)
