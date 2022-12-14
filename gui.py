import threading
from dearpygui.dearpygui import *
from config import ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG, KEYBOARD_CONFIG, LANDSCAPE_NUM_CONFIG, MIDI_CONFIG, MIDI_PORT_CONFIG, get_config, set_config, PATH_CONFIG
from midi import Midi
import tile as T

WIDTH = 450
HEIGHT = 600

selected_item = None
render_thread: threading.Thread = None


def setup_gui():
    create_context()
    create_viewport(min_width=WIDTH, min_height=HEIGHT,
                    width=WIDTH, height=HEIGHT, title='Tyler - Config')
    setup_dearpygui()
    set_viewport_small_icon('./statics/tile-icon.ico')
    set_viewport_large_icon('./statics/tile-icon.ico')


def file_selection_callback(s, a, u):
    set_config(PATH_CONFIG, a['file_path_name'])
    set_item_label(u, f'Select sources: {get_config(PATH_CONFIG)}')


def is_rendering() -> bool:
    global render_thread
    return render_thread is not None and render_thread.is_alive()


def start_callback(s, a, u):
    global render_thread
    if (not is_rendering()):
        render_thread = threading.Thread(group=None, target=T.render, args=[u])
        render_thread.start()


def key_down_callback(s, a, u):
    global selected_item
    if selected_item is None:
        return
    key = chr(a[0]).upper()
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    for i in range(len(u)):
        item = u[i]
        if item == selected_item:
            key_map[i] = key
            set_config(KEYBOARD_CONFIG, key_map)
            set_item_label(selected_item, f'{midi_map[i]} | {key_map[i]}')
    set_value(selected_item, False)
    selected_item = None


def midi_down_callback(midi: Midi, items: list):
    global selected_item
    if selected_item is None:
        return
    note = midi.get_midi_note()
    if note is None:
        return
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    for i in range(len(items)):
        item = items[i]
        if item == selected_item:
            midi_map[i] = note
            set_config(MIDI_CONFIG, midi_map)
            set_item_label(selected_item, f'{midi_map[i]} | {key_map[i]}')
    set_value(selected_item, False)
    selected_item = None


def resize_callback(s, a, u):
    print(s)
    print(a)
    print(u)


def select_callback(s, a, u):
    global selected_item
    for i in range(len(u)):
        item = u[i]
        if item != s:
            set_value(item, False)
    if s == selected_item:
        selected_item = None
    else:
        selected_item = s


def num_input_callback(s, a, u):
    set_config(u, a)


def tuple_input_callback(s, a, u):
    value = get_config(ASPECT_RATIO_CONFIG)
    value[u] = a
    set_config(ASPECT_RATIO_CONFIG, value)


def add_left_input_int(label='', callback=lambda s, a, u: None, default_value=0, user_data=None):
    ret = 0
    with group(horizontal=True):
        add_text(label)
        ret = add_input_int(callback=callback,
                            default_value=default_value,
                            width=100, user_data=user_data)
    return ret


def add_left_input_float(label='', callback=lambda s, a, u: None, default_value=0, user_data=None):
    ret = 0
    with group(horizontal=True):
        add_text(label)
        ret = add_input_float(callback=callback,
                              default_value=default_value,
                              width=100, user_data=user_data)
    return ret


def add_input_tuple(label='', callback=lambda s, a, u: None, default_value=(0, 0)):
    add_text(label)
    add_left_input_int(
        label='Width', callback=callback, default_value=default_value[0], user_data=0)
    add_left_input_int(
        label='Height', callback=callback, default_value=default_value[1], user_data=1)


def draw_gui(midi: Midi):
    setup_gui()

    button = None
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    items = []
    with window(tag='primary', width=WIDTH, height=HEIGHT, no_title_bar=True, no_move=True, no_close=True, no_resize=True, no_collapse=True):
        with tree_node(label='VIDEO') as video_config:
            set_value(video_config, True)
            add_left_input_int(label='Landscapes', callback=num_input_callback,
                               default_value=get_config(LANDSCAPE_NUM_CONFIG), user_data=LANDSCAPE_NUM_CONFIG)
            button = add_button(label=f'Select sources: {get_config(PATH_CONFIG)}', user_data=last_container(),
                                callback=lambda s, a, u: show_item(
                                    'file_dialog'),
                                tag='file_button')
            add_input_tuple(label='Aspect Ratio', callback=tuple_input_callback,
                            default_value=get_config(ASPECT_RATIO_CONFIG))
            add_left_input_float(label='Framerate', callback=num_input_callback,
                                 default_value=get_config(FRAMERATE_CONFIG), user_data=FRAMERATE_CONFIG)
        with tree_node(label='MIDI') as midi_config:
            set_value(midi_config, True)
            add_left_input_int(label='Midi Port', callback=num_input_callback,
                               default_value=get_config(MIDI_PORT_CONFIG), user_data=MIDI_PORT_CONFIG)
            add_text('Define control for each section: (midi | keyboard)')
            with table(header_row=False, borders_outerH=True,
                       borders_outerV=True, width=240, height=160):
                add_table_column()
                add_table_column()
                add_table_column()

                with table_row():
                    items.append(add_selectable(label=f'{midi_map[0]} | {key_map[0]}', width=75, height=75,
                                                callback=select_callback))
                    items.append(add_selectable(label=f'{midi_map[1]} | {key_map[1]}', width=75, height=75,
                                                callback=select_callback))
                    items.append(add_selectable(label=f'{midi_map[2]} | {key_map[2]}', width=75, height=75,
                                                callback=select_callback))

                with table_row():
                    items.append(add_selectable(label=f'{midi_map[3]} | {key_map[3]}', width=75, height=75,
                                                callback=select_callback))
                    items.append(add_selectable(label=f'{midi_map[4]} | {key_map[4]}', width=75, height=75,
                                                callback=select_callback))
                    items.append(add_selectable(label=f'{midi_map[5]} | {key_map[5]}', width=75, height=75,
                                                callback=select_callback))

        for item in items:
            configure_item(item, user_data=items)

        add_button(label='Start', callback=start_callback, user_data=midi)

    with handler_registry():
        add_key_down_handler(callback=key_down_callback, user_data=items)
        # add_resize_handler(callback=resize_callback)
    add_file_dialog(label="Select scenes directory...",
                    directory_selector=True, callback=file_selection_callback,
                    show=False, modal=True, tag='file_dialog', user_data=button,
                    width=0.9*WIDTH, height=0.75*HEIGHT)
    show_viewport()
    set_primary_window('primary', True)
    while is_dearpygui_running():
        midi_down_callback(midi, items)
        render_dearpygui_frame()
    destroy_gui()


def destroy_gui():
    global render_thread
    if (is_rendering()):
        render_thread.join()
    destroy_context()
