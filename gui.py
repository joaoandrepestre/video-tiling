from locale import atoi
from dearpygui.dearpygui import *
from config import KEYBOARD_CONFIG, MIDI_CONFIG, get_config, set_config, PATH_CONFIG
from midi import Midi

WIDTH = 450
HEIGHT = 600

should_start = False
selected_item = None


def setup_gui():
    create_context()
    create_viewport(width=WIDTH, height=HEIGHT, title='Tyler - Config')
    setup_dearpygui()


def file_selection_callback(s, a, u):
    set_config(PATH_CONFIG, a['file_path_name'])
    set_item_label(u, f'Select sources: {get_config(PATH_CONFIG)}')


def start_callback():
    global should_start
    should_start = True


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


def draw_gui(midi: Midi) -> bool:
    global should_start
    button = None
    midi_map = get_config(MIDI_CONFIG)
    key_map = get_config(KEYBOARD_CONFIG)
    items = []
    with window(width=WIDTH, height=HEIGHT, no_title_bar=True, no_move=True, no_close=True, no_resize=True, no_collapse=True):
        button = add_button(label=f'Select sources: {get_config(PATH_CONFIG)}', user_data=last_container(),
                            callback=lambda s, a, u: show_item('file_dialog'),
                            tag='file_button')
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

        add_button(label='Start', callback=start_callback)

    with handler_registry():
        add_key_down_handler(callback=key_down_callback, user_data=items)
    add_file_dialog(label="Select scenes directory...",
                    directory_selector=True, callback=file_selection_callback,
                    show=False, modal=True, tag='file_dialog', user_data=button,
                    width=0.9*WIDTH, height=0.75*HEIGHT)
    show_viewport()
    while is_dearpygui_running():
        if should_start:
            break
        midi_down_callback(midi, items)
        render_dearpygui_frame()
    return should_start


def destroy_gui():
    destroy_context()
