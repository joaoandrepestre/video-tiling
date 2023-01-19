import threading
from dearpygui.dearpygui import *
from config import ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG, KEYBOARD_CONFIG, LANDSCAPE_NUM_CONFIG, MIDI_CONFIG, MIDI_PORT_CONFIG, get_config, set_config, PATH_CONFIG, DEFAULT_CONFIG, KNOB_CONFIG
from midi import Midi, MidiMessageType
import tile as T

WIDTH = 450
HEIGHT = 600

midi_items: list = []
selected_item = None
render_thread: threading.Thread = None
framerate_input = None


def setup_gui(midi: Midi):
    create_context()
    create_viewport(min_width=WIDTH, min_height=HEIGHT,
                    width=WIDTH, height=HEIGHT, title='Tyler - Config')
    setup_dearpygui()
    set_viewport_small_icon('./statics/tile-icon.ico')
    set_viewport_large_icon('./statics/tile-icon.ico')
    midi.subscribe(MidiMessageType.NOTE_ON, midi_note_handler)
    midi.subscribe(MidiMessageType.CONTROL_CHANGE, midi_knob_handler)


def midi_knob_handler(knob: int, value: int) -> None:
    global framerate_input
    knob_config = get_config(KNOB_CONFIG)
    if (framerate_input is None):
        return
    if (knob != knob_config):
        return
    default = DEFAULT_CONFIG[FRAMERATE_CONFIG]
    nfr = (value / 127.0) * default + default / 2.0
    set_config(FRAMERATE_CONFIG, nfr)
    set_value(framerate_input, nfr)


def midi_note_handler(note: int, velocity: int) -> None:
    global midi_items, selected_item
    if selected_item is None:
        return
    if (velocity == 0):
        return
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    for i in range(len(midi_items)):
        item = midi_items[i]
        if item == selected_item:
            midi_map[i] = f'{note}'
            set_config(MIDI_CONFIG, midi_map)
            set_item_label(selected_item, f'{midi_map[i]} | {key_map[i]}')
    set_value(selected_item, False)
    selected_item = None


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


def midi_retry_connection(midi: Midi, midi_status: int | None):
    res = midi.is_device_connected()
    label = 'Connected' if res else 'Disconnected'
    color = [0, 255, 0] if res else [255, 0, 0]
    set_value(midi_status, label)
    configure_item(midi_status, color=color)


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
    global midi_items, framerate_input
    setup_gui(midi)

    button = None
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    items = []
    midi_status = None
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
            framerate_input = add_left_input_float(label='Framerate', callback=num_input_callback,
                                                   default_value=get_config(FRAMERATE_CONFIG), user_data=FRAMERATE_CONFIG)
        with tree_node(label='MIDI') as midi_config:
            with group(horizontal=True):
                add_text('Status: ')
                midi_status = add_text(f'Disconnected', color=[255, 0, 0])
            set_value(midi_config, True)
            add_left_input_int(label='Midi Port', callback=num_input_callback,
                               default_value=get_config(MIDI_PORT_CONFIG), user_data=MIDI_PORT_CONFIG)
            add_left_input_int(label='Framerate Knob', callback=num_input_callback,
                               default_value=get_config(KNOB_CONFIG), user_data=KNOB_CONFIG)
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
        midi_items = items

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
        midi_retry_connection(midi, midi_status)
        render_dearpygui_frame()
    destroy_gui()


def destroy_gui():
    global render_thread
    if (is_rendering()):
        render_thread.join()
    destroy_context()
