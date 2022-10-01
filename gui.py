import dearpygui.dearpygui as dpg

WIDTH = 450
HEIGHT = 600
PATH = ""


def setup_gui():
    dpg.create_context()
    dpg.create_viewport(width=WIDTH, height=HEIGHT, title='Tyler')
    dpg.setup_dearpygui()


def file_selection_callback(s, a, u):
    global PATH
    PATH = a['file_path_name']
    dpg.set_item_label(u, f'Select sources: {PATH}')


def draw_gui():
    button = None
    with dpg.window(width=WIDTH, height=HEIGHT, no_title_bar=True, no_move=True, no_close=True, no_resize=True, no_collapse=True):
        button = dpg.add_button(label="Select sources: ", user_data=dpg.last_container(),
                                callback=lambda s, a, u: dpg.show_item('file_dialog'), tag='file_button')
    dpg.add_file_dialog(label="Select scenes directory...",
                        directory_selector=True, callback=file_selection_callback,
                        show=False, modal=True, tag='file_dialog', user_data=button,
                        width=0.9*WIDTH, height=0.75*HEIGHT)
    dpg.show_viewport()
    dpg.start_dearpygui()


def destroy_gui():
    dpg.destroy_context()
