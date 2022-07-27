cometrics_version = "1.2.6.6"
ui_title = f"cometrics v{cometrics_version}"

cometrics_data_root = fr'C:\cometrics'
cometrics_ver_root = fr'{cometrics_data_root}\{cometrics_version}'

project_treeview_params = [40, 60, 400, 300]

ksf_distance = 1.75
window_ratio = 0.7

large_header_font = ('Purisa', 16)
large_treeview_font = ('Purisa', 16, 'bold')
large_treeview_rowheight = 28
large_field_font = ('Purisa', 14)
large_field_offset = 70
large_button_size = (120, 35)
large_tab_size = (140, 35)

medium_header_font = ('Purisa', 14)
medium_treeview_font = ('Purisa', 14, 'bold')
medium_treeview_rowheight = 25
medium_field_font = ('Purisa', 12)
medium_field_offset = 60
medium_button_size = (100, 30)
medium_tab_size = (120, 30)

small_header_font = ('Purisa', 12)
small_treeview_font = ('Purisa', 12, 'bold')
small_treeview_rowheight = 18
small_field_font = ('Purisa', 10)
small_field_offset = 50
small_button_size = (80, 25)
small_tab_size = (110, 25)

treeview_tags = ['odd', 'even', 'header']
treeview_default_tag_dict = {
    'odd': '#E8E8E8',
    'even': '#DFDFDF',
    'header': '#C4C4C4'
}
treeview_bind_tags = ['odd', 'even', 'toggle']
treeview_bind_tag_dict = {
    'odd': '#E8E8E8',
    'even': '#DFDFDF',
    'toggle': 'red'
}

# https://unicode-table.com/en/#274E
checkmark = '\u2705'
crossmark = '\u274E'
