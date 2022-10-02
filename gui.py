from dearpygui.dearpygui import *
from config import get_config, set_config, PATH_CONFIG

WIDTH = 450
HEIGHT = 600

should_start = False


def setup_gui():
    create_context()
    create_viewport(width=WIDTH, height=HEIGHT, title='Tyler')
    setup_dearpygui()


def file_selection_callback(s, a, u):
    set_config(PATH_CONFIG, a['file_path_name'])
    set_item_label(u, f'Select sources: {get_config(PATH_CONFIG)}')


def start_callback():
    global should_start
    should_start = True


def draw_gui() -> bool:
    global should_start
    button = None
    with window(width=WIDTH, height=HEIGHT, no_title_bar=True, no_move=True, no_close=True, no_resize=True, no_collapse=True):
        button = add_button(label=f'Select sources: {get_config(PATH_CONFIG)}', user_data=last_container(),
                            callback=lambda s, a, u: show_item('file_dialog'),
                            tag='file_button')
        add_button(label='Start', callback=start_callback)
    add_file_dialog(label="Select scenes directory...",
                    directory_selector=True, callback=file_selection_callback,
                    show=False, modal=True, tag='file_dialog', user_data=button,
                    width=0.9*WIDTH, height=0.75*HEIGHT)
    show_viewport()
    while is_dearpygui_running():
        if should_start:
            break
        render_dearpygui_frame()
    return should_start


def destroy_gui():
    cleanup_dearpygui()
