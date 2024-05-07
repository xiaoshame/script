#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Youtubedlg module responsible for the options window. """

from __future__ import unicode_literals

import os

import wx
import wx.adv
from utils import get_icon_file
from wx.lib.art import flagart

from formats import AUDIO_FORMATS, OUTPUT_FORMATS, VIDEO_FORMATS
from utils import os_path_exists,tdict,os_sep
from info import __appname__

#REFACTOR Move all formats, etc to formats.py


class OptionsFrame(wx.Frame):

    """Youtubedlg options frame class.

    Args:
        parent (mainframe.MainFrame): Parent class.

    """

    FRAME_TITLE = ("Options")

    FRAMES_MIN_SIZE = (500, 470)

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title=self.FRAME_TITLE, size=parent.opt_manager.options["opts_win_size"])
        self.opt_manager = parent.opt_manager
        self.log_manager = parent.log_manager
        self.app_icon = None

        # Set the app icon
        #REFACTOR Get icon from parent
        app_icon_path = get_icon_file()
        if app_icon_path is not None:
            self.app_icon = wx.Icon(app_icon_path, wx.BITMAP_TYPE_ICO)
            self.SetIcon(self.app_icon)

        self._was_shown = False

        # Create options frame basic components
        self.panel = wx.Panel(self)

        self.notebook = wx.Notebook(self.panel)
        self.separator_line = wx.StaticLine(self.panel)
        self.reset_button = wx.Button(self.panel, label=("重置"))
        self.close_button = wx.Button(self.panel, label=("关闭"))

        # 创建标签页
        tab_args = (self, self.notebook)

        self.tabs = (
            (GeneralTab(*tab_args), ("常规")),
            (FormatsTab(*tab_args), ("格式")),
            (DownloadsTab(*tab_args), ("下载")),
            (AdvancedTab(*tab_args), ("高级")),
            (ExtraTab(*tab_args), ("其他"))
        )

        # Add tabs on notebook
        for tab, label in self.tabs:
            self.notebook.AddPage(tab, label)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self._on_reset, self.reset_button)
        self.Bind(wx.EVT_BUTTON, self._on_close, self.close_button)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self.SetMinSize(self.FRAMES_MIN_SIZE)

        self._set_layout()
        self.load_all_options()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, border=5)
        main_sizer.Add(self.separator_line, 0, wx.EXPAND)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(self.reset_button)
        buttons_sizer.AddSpacer(5)
        buttons_sizer.Add(self.close_button)

        main_sizer.Add(buttons_sizer, flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

        self.panel.SetSizer(main_sizer)

        self.panel.Layout()

    def _on_close(self, event):
        """Event handler for wx.EVT_CLOSE event."""
        self.save_all_options()
        #REFACTOR Parent create specific callback
        self.GetParent()._update_videoformat_combobox()
        self.Hide()

    def _on_reset(self, event):
        """Event handler for the reset button wx.EVT_BUTTON event."""
        self.reset()
        self.GetParent().reset()

    def reset(self):
        """Reset the default options."""
        self.opt_manager.load_default()
        self.load_all_options()

    def load_all_options(self):
        """Load all the options on each tab."""
        for tab, _ in self.tabs:
            tab.load_options()

    def save_all_options(self):
        """Save all the options from all the tabs back to the OptionsManager."""
        for tab, _ in self.tabs:
            tab.save_options()

    def Show(self, *args, **kwargs):
        # CenterOnParent can't go to main frame's __init__ as main frame may change
        # own position and options frame won't be centered on main frame anymore.
        if not self._was_shown:
            self._was_shown = True
            self.CenterOnParent()
        return wx.Frame.Show(self, *args, **kwargs)


class TabPanel(wx.Panel):

    """Main tab class from which each tab inherits.

    Args:
        parent (OptionsFrame): The parent of all tabs.

        notebook (wx.Notebook): The container for each tab.

    Notes:
        In order to use a different size you must overwrite the below *_SIZE
        attributes on the corresponding child object.

    """

    CHECKBOX_SIZE = (-1, -1)
    if os.name == "nt":
        # Make checkboxes look the same on Windows
        CHECKBOX_SIZE = (-1, 25)

    BUTTONS_SIZE = (-1, -1)
    TEXTCTRL_SIZE = (-1, -1)
    SPINCTRL_SIZE = (70, -1)

    CHECKLISTBOX_SIZE = (-1, 80)
    LISTBOX_SIZE = (-1, 80)

    def __init__(self, parent, notebook):
        super(TabPanel, self).__init__(notebook)
        #REFACTOR Maybe add methods to access those
        #save_options(key, value)
        #load_options(key)
        self.opt_manager = parent.opt_manager
        self.log_manager = parent.log_manager
        self.app_icon = parent.app_icon

        self.reset_handler = parent.reset

    # Shortcut methods below

    def crt_button(self, label, event_handler=None):
        button = wx.Button(self, label=label, size=self.BUTTONS_SIZE)

        if event_handler is not None:
            button.Bind(wx.EVT_BUTTON, event_handler)

        return button

    def crt_checkbox(self, label, event_handler=None):
        checkbox = wx.CheckBox(self, label=label, size=self.CHECKBOX_SIZE)

        if event_handler is not None:
            checkbox.Bind(wx.EVT_CHECKBOX, event_handler)

        return checkbox

    def crt_textctrl(self, style=None):
        if style is None:
            textctrl = wx.TextCtrl(self, size=self.TEXTCTRL_SIZE)
        else:
            textctrl = wx.TextCtrl(self, size=self.TEXTCTRL_SIZE, style=style)

        return textctrl

    def crt_combobox(self, choices, size=(-1, -1), event_handler=None):
        combobox = wx.ComboBox(self, choices=choices, size=size, style=wx.CB_READONLY)

        if event_handler is not None:
            combobox.Bind(wx.EVT_COMBOBOX, event_handler)

        return combobox

    def crt_bitmap_combobox(self, choices, size=(-1, -1), event_handler=None):
        combobox = wx.adv.BitmapComboBox(self, size=size, style=wx.CB_READONLY)

        for item in choices:
            lang_code, lang_name = item

            _, country = lang_code.split('_')
            if country in flagart.catalog:
                flag_bmp = flagart.catalog[country].GetBitmap()
            else:
                flag_bmp = flagart.catalog["BLANK"].GetBitmap()

            combobox.Append(lang_name, flag_bmp)

        if event_handler is not None:
            combobox.Bind(wx.EVT_COMBOBOX, event_handler)

        return combobox

    def crt_spinctrl(self, spin_range=(0, 9999)):
        spinctrl = wx.SpinCtrl(self, size=self.SPINCTRL_SIZE)
        spinctrl.SetRange(*spin_range)

        return spinctrl

    def crt_statictext(self, label):
        return wx.StaticText(self, wx.ID_ANY, label)

    def crt_staticbox(self, label):
        return wx.StaticBox(self, wx.ID_ANY, label)

    def crt_checklistbox(self, choices, style=None):
        if style is None:
            checklistbox = wx.CheckListBox(self, choices=choices, size=self.CHECKLISTBOX_SIZE)
        else:
            checklistbox = wx.CheckListBox(self, choices=choices, style=style, size=self.CHECKLISTBOX_SIZE)

        return checklistbox

    def crt_listbox(self, choices, style=None):
        if style is None:
            listbox = wx.ListBox(self, choices=choices, size=self.LISTBOX_SIZE)
        else:
            listbox = wx.ListBox(self, choices=choices, style=style, size=self.LISTBOX_SIZE)

        return listbox


class GeneralTab(TabPanel):

    OUTPUT_TEMPLATES = [
        "ID",
        "标题",
        "扩展名",
        "上传者",
        "分辨率",
        "自动编号",
        "",
        "观看次数",
        "点赞数",
        "点踩数",
        "评论数",
        "平均评分",
        "年龄限制",
        "宽度",
        "高度",
        "提取器",
        "",
        "播放列表",
        "播放列表索引",
    ]

    BUTTONS_SIZE = (30, -1)

    def __init__(self, *args, **kwargs):
        super(GeneralTab, self).__init__(*args, **kwargs)

        self.filename_format_label = self.crt_statictext(("文件名格式"))
        self.filename_format_combobox = self.crt_combobox(list(OUTPUT_FORMATS.values()), event_handler=self._on_filename)
        self.filename_custom_format = self.crt_textctrl()
        self.filename_custom_format_button = self.crt_button("...", self._on_format)

        self.filename_opts_label = self.crt_statictext(("文件名选项"))
        self.filename_ascii_checkbox = self.crt_checkbox(("仅限ASCII字符作为文件名"))

        self.more_opts_label = self.crt_statictext(("更多选项"))
        self.confirm_exit_checkbox = self.crt_checkbox(("退出时确认"))
        self.confirm_deletion_checkbox = self.crt_checkbox(("删除项目时确认"))
        self.show_completion_popup_checkbox = self.crt_checkbox(("下载完成后通知我"))

        self.shutdown_checkbox = self.crt_checkbox(("下载完成后关机"), event_handler=self._on_shutdown)
        self.sudo_textctrl = self.crt_textctrl(wx.TE_PASSWORD)

        # Build the menu for the custom format button
        self.custom_format_menu = self._build_custom_format_menu()

        self._set_layout()

        if os.name == "nt":
            self.sudo_textctrl.Hide()

        self.sudo_textctrl.SetToolTip(wx.ToolTip(("SUDO password")))

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.filename_format_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.filename_format_combobox, flag=wx.EXPAND | wx.ALL, border=5)

        custom_format_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_format_sizer.Add(self.filename_custom_format, 1, wx.ALIGN_CENTER_VERTICAL)
        custom_format_sizer.AddSpacer(5)
        custom_format_sizer.Add(self.filename_custom_format_button)

        vertical_sizer.Add(custom_format_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        vertical_sizer.Add(self.filename_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.filename_ascii_checkbox, flag=wx.ALL, border=5)

        vertical_sizer.Add(self.more_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.confirm_exit_checkbox, flag=wx.ALL, border=5)
        vertical_sizer.Add(self.confirm_deletion_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        vertical_sizer.Add(self.show_completion_popup_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        shutdown_sizer = wx.BoxSizer(wx.HORIZONTAL)
        shutdown_sizer.Add(self.shutdown_checkbox)
        shutdown_sizer.AddSpacer(1)
        shutdown_sizer.Add(self.sudo_textctrl, 1)

        vertical_sizer.Add(shutdown_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def _build_custom_format_menu(self):
        menu = wx.Menu()

        for template in self.OUTPUT_TEMPLATES:
            if template:
                menu_item = menu.Append(wx.ID_ANY, template)
                menu.Bind(wx.EVT_MENU, self._on_template, menu_item)
            else:
                menu.AppendSeparator()

        return menu

    def _on_template(self, event):
        """Event handler for the wx.EVT_MENU of the custom_format_menu menu items."""
        label = self.custom_format_menu.GetLabelText(event.GetId())
        label = label.lower().replace(' ', '_')

        custom_format = self.filename_custom_format.GetValue()

        if label == "ext":
            prefix = '.'
        else:
            prefix = '-'

        if not custom_format or custom_format[-1] == os_sep:
            # If the custom format is empty or ends with path separator
            # remove the prefix
            prefix = ''

        template = "{0}%({1})s".format(prefix, label)
        self.filename_custom_format.SetValue(custom_format + template)

    def _on_format(self, event):
        """Event handler for the wx.EVT_BUTTON of the filename_custom_format_button."""
        event_object_pos = event.EventObject.GetPosition()
        event_object_height = event.EventObject.GetSize()[1]
        event_object_pos = (event_object_pos[0], event_object_pos[1] + event_object_height)
        self.PopupMenu(self.custom_format_menu, event_object_pos)

    def _on_filename(self, event):
        """Event handler for the wx.EVT_COMBOBOX of the filename_format_combobox."""
        custom_selected = self.filename_format_combobox.GetValue() == OUTPUT_FORMATS[3]

        self.filename_custom_format.Enable(custom_selected)
        self.filename_custom_format_button.Enable(custom_selected)

    def _on_shutdown(self, event):
        """Event handler for the wx.EVT_CHECKBOX of the shutdown_checkbox."""
        self.sudo_textctrl.Enable(self.shutdown_checkbox.GetValue())

    def load_options(self):
        self.filename_format_combobox.SetValue(OUTPUT_FORMATS[self.opt_manager.options["output_format"]])
        self.filename_custom_format.SetValue(self.opt_manager.options["output_template"])
        self.filename_ascii_checkbox.SetValue(self.opt_manager.options["restrict_filenames"])
        self.shutdown_checkbox.SetValue(self.opt_manager.options["shutdown"])
        self.sudo_textctrl.SetValue(self.opt_manager.options["sudo_password"])
        self.confirm_exit_checkbox.SetValue(self.opt_manager.options["confirm_exit"])
        self.show_completion_popup_checkbox.SetValue(self.opt_manager.options["show_completion_popup"])
        self.confirm_deletion_checkbox.SetValue(self.opt_manager.options["confirm_deletion"])

        #REFACTOR Automatically call on the new methods
        #save_options
        #load_options
        #NOTE Maybe on init add callback?
        self._on_filename(None)
        self._on_shutdown(None)

    def save_options(self):
        self.opt_manager.options["output_format"] = tdict(OUTPUT_FORMATS)[self.filename_format_combobox.GetValue()]
        self.opt_manager.options["output_template"] = self.filename_custom_format.GetValue()
        self.opt_manager.options["restrict_filenames"] = self.filename_ascii_checkbox.GetValue()
        self.opt_manager.options["shutdown"] = self.shutdown_checkbox.GetValue()
        self.opt_manager.options["sudo_password"] = self.sudo_textctrl.GetValue()
        self.opt_manager.options["confirm_exit"] = self.confirm_exit_checkbox.GetValue()
        self.opt_manager.options["show_completion_popup"] = self.show_completion_popup_checkbox.GetValue()
        self.opt_manager.options["confirm_deletion"] = self.confirm_deletion_checkbox.GetValue()


class FormatsTab(TabPanel):

    AUDIO_QUALITY = dict([("0", ("high")), ("5", ("mid")), ("9", ("low"))])

    def __init__(self, *args, **kwargs):
        super(FormatsTab, self).__init__(*args, **kwargs)

        self.video_formats_label = self.crt_statictext(("视频格式"))
        self.video_formats_checklistbox = self.crt_checklistbox(list(VIDEO_FORMATS.values()))

        self.audio_formats_label = self.crt_statictext(("音频格式"))
        self.audio_formats_checklistbox = self.crt_checklistbox(list(AUDIO_FORMATS.values()))

        self.post_proc_opts_label = self.crt_statictext(("后期处理选项"))
        self.keep_video_checkbox = self.crt_checkbox(("保留原始文件"))
        self.extract_audio_checkbox = self.crt_checkbox(("从视频文件中提取音频"))
        self.embed_thumbnail_checkbox = self.crt_checkbox(("在音频文件中嵌入缩略图"))
        self.add_metadata_checkbox = self.crt_checkbox(("向文件添加元数据"))

        self.audio_quality_label = self.crt_statictext(("音频质量"))
        self.audio_quality_combobox = self.crt_combobox(list(self.AUDIO_QUALITY.values()))

        self._set_layout()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.video_formats_label)
        vertical_sizer.Add(self.video_formats_checklistbox, 1, wx.EXPAND | wx.ALL, border=5)

        vertical_sizer.Add(self.audio_formats_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.audio_formats_checklistbox, 1, wx.EXPAND | wx.ALL, border=5)

        vertical_sizer.Add(self.post_proc_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.keep_video_checkbox, flag=wx.ALL, border=5)
        vertical_sizer.Add(self.extract_audio_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        vertical_sizer.Add(self.embed_thumbnail_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)
        vertical_sizer.Add(self.add_metadata_checkbox, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        audio_quality_sizer = wx.BoxSizer(wx.HORIZONTAL)
        audio_quality_sizer.Add(self.audio_quality_label, flag=wx.ALIGN_CENTER_VERTICAL)
        audio_quality_sizer.AddSpacer(20)
        audio_quality_sizer.Add(self.audio_quality_combobox)

        vertical_sizer.Add(audio_quality_sizer, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def load_options(self):
        checked_video_formats = [VIDEO_FORMATS[vformat] for vformat in self.opt_manager.options["selected_video_formats"]]
        self.video_formats_checklistbox.SetCheckedStrings(checked_video_formats)
        checked_audio_formats = [AUDIO_FORMATS[aformat] for aformat in self.opt_manager.options["selected_audio_formats"]]
        self.audio_formats_checklistbox.SetCheckedStrings(checked_audio_formats)
        self.keep_video_checkbox.SetValue(self.opt_manager.options["keep_video"])
        self.audio_quality_combobox.SetValue(self.AUDIO_QUALITY[self.opt_manager.options["audio_quality"]])
        self.extract_audio_checkbox.SetValue(self.opt_manager.options["to_audio"])
        self.embed_thumbnail_checkbox.SetValue(self.opt_manager.options["embed_thumbnail"])
        self.add_metadata_checkbox.SetValue(self.opt_manager.options["add_metadata"])

    def save_options(self):
        checked_video_formats = [VIDEO_FORMATS[vformat] for vformat in self.video_formats_checklistbox.GetCheckedStrings()]
        self.opt_manager.options["selected_video_formats"] = checked_video_formats
        checked_audio_formats = [AUDIO_FORMATS[aformat] for aformat in self.audio_formats_checklistbox.GetCheckedStrings()]
        self.opt_manager.options["selected_audio_formats"] = checked_audio_formats
        self.opt_manager.options["keep_video"] = self.keep_video_checkbox.GetValue()
        self.opt_manager.options["audio_quality"] = tdict(self.AUDIO_QUALITY)[self.audio_quality_combobox.GetValue()]
        self.opt_manager.options["to_audio"] = self.extract_audio_checkbox.GetValue()
        self.opt_manager.options["embed_thumbnail"] = self.embed_thumbnail_checkbox.GetValue()
        self.opt_manager.options["add_metadata"] = self.add_metadata_checkbox.GetValue()


class DownloadsTab(TabPanel):

    # Lang code = ISO 639-1
    SUBS_LANG = dict([
        ("en", ("English")),
        ("fr", ("French")),
        ("de", ("German")),
        ("el", ("Greek")),
        ("he", ("Hebrew")),
        ("it", ("Italian")),
        ("pt", ("Portuguese")),
        ("ru", ("Russian")),
        ("es", ("Spanish")),
        ("sv", ("Swedish")),
        ("tr", ("Turkish"))
    ])

    FILESIZES = dict([
        ("", "Bytes"),
        ("k", "Kilobytes"),
        ("m", "Megabytes"),
        ("g", "Gigabytes"),
        ("t", "Terabytes"),
        ("p", "Petabytes"),
        ("e", "Exabytes"),
        ("z", "Zettabytes"),
        ("y", "Yottabytes")
    ])

    SUBS_CHOICES = [
        ("无"),
        ("自动字幕（仅限 YOUTUBE）"),
        ("所有可用字幕"),
        ("按语言选择字幕")
    ]

    def __init__(self, *args, **kwargs):
        super(DownloadsTab, self).__init__(*args, **kwargs)

        self.subtitles_label = self.crt_statictext(("字幕"))
        self.subtitles_combobox = self.crt_combobox(self.SUBS_CHOICES, event_handler=self._on_subtitles)
        self.subtitles_lang_listbox = self.crt_listbox(list(self.SUBS_LANG.values()))

        self.subtitles_opts_label = self.crt_statictext(("字幕选项"))
        self.embed_subs_checkbox = self.crt_checkbox(("将字幕嵌入到视频文件（仅限 mp4）"))

        self.playlist_box = self.crt_staticbox(("播放列表"))

        self.playlist_start_label = self.crt_statictext(("开始"))
        self.playlist_start_spinctrl = self.crt_spinctrl((1, 9999))
        self.playlist_stop_label = self.crt_statictext(("停止"))
        self.playlist_stop_spinctrl = self.crt_spinctrl()
        self.playlist_max_label = self.crt_statictext(("最大"))
        self.playlist_max_spinctrl = self.crt_spinctrl()

        self.filesize_box = self.crt_staticbox(("文件大小"))

        self.filesize_max_label = self.crt_statictext(("最大"))
        self.filesize_max_spinctrl = self.crt_spinctrl((0, 1024))
        self.filesize_max_sizeunit_combobox = self.crt_combobox(list(self.FILESIZES.values()))
        self.filesize_min_label = self.crt_statictext(("最小"))
        self.filesize_min_spinctrl = self.crt_spinctrl((0, 1024))
        self.filesize_min_sizeunit_combobox = self.crt_combobox(list(self.FILESIZES.values()))

        self._set_layout()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.subtitles_label)
        vertical_sizer.Add(self.subtitles_combobox, flag=wx.EXPAND | wx.ALL, border=5)
        vertical_sizer.Add(self.subtitles_lang_listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

        vertical_sizer.Add(self.subtitles_opts_label, flag=wx.TOP, border=5)
        vertical_sizer.Add(self.embed_subs_checkbox, flag=wx.ALL, border=5)

        plist_and_fsize_sizer = wx.BoxSizer(wx.HORIZONTAL)
        plist_and_fsize_sizer.Add(self._build_playlist_sizer(), 1, wx.EXPAND)
        plist_and_fsize_sizer.AddSpacer(5)
        plist_and_fsize_sizer.Add(self._build_filesize_sizer(), 1, wx.EXPAND)

        vertical_sizer.Add(plist_and_fsize_sizer, 1, wx.EXPAND | wx.TOP, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def _build_playlist_sizer(self):
        playlist_box_sizer = wx.StaticBoxSizer(self.playlist_box, wx.VERTICAL)
        playlist_box_sizer.AddSpacer(10)

        border = wx.GridBagSizer(5, 40)

        border.Add(self.playlist_start_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_start_spinctrl, (0, 1))

        border.Add(self.playlist_stop_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_stop_spinctrl, (1, 1))

        border.Add(self.playlist_max_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(self.playlist_max_spinctrl, (2, 1))

        playlist_box_sizer.Add(border, flag=wx.ALIGN_CENTER)

        return playlist_box_sizer

    def _build_filesize_sizer(self):
        filesize_box_sizer = wx.StaticBoxSizer(self.filesize_box, wx.VERTICAL)

        border = wx.GridBagSizer(5, 20)

        border.Add(self.filesize_max_label, (0, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

        border.Add(self.filesize_max_spinctrl, (1, 0))
        border.Add(self.filesize_max_sizeunit_combobox, (1, 1))

        border.Add(self.filesize_min_label, (2, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

        border.Add(self.filesize_min_spinctrl, (3, 0))
        border.Add(self.filesize_min_sizeunit_combobox, (3, 1))

        filesize_box_sizer.Add(border, flag=wx.ALIGN_CENTER)

        return filesize_box_sizer

    def _on_subtitles(self, event):
        """Event handler for the wx.EVT_COMBOBOX of the subtitles_combobox."""
        self.subtitles_lang_listbox.Enable(self.subtitles_combobox.GetValue() == self.SUBS_CHOICES[-1])

    def load_options(self):
        #NOTE Find a better way to do this
        if self.opt_manager.options["write_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[3])
        elif self.opt_manager.options["write_all_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[2])
        elif self.opt_manager.options["write_auto_subs"]:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[1])
        else:
            self.subtitles_combobox.SetValue(self.SUBS_CHOICES[0])

        self.subtitles_lang_listbox.SetStringSelection(self.SUBS_LANG[self.opt_manager.options["subs_lang"]])
        self.embed_subs_checkbox.SetValue(self.opt_manager.options["embed_subs"])
        self.playlist_start_spinctrl.SetValue(self.opt_manager.options["playlist_start"])
        self.playlist_stop_spinctrl.SetValue(self.opt_manager.options["playlist_end"])
        self.playlist_max_spinctrl.SetValue(self.opt_manager.options["max_downloads"])
        self.filesize_min_spinctrl.SetValue(self.opt_manager.options["min_filesize"])
        self.filesize_max_spinctrl.SetValue(self.opt_manager.options["max_filesize"])
        self.filesize_min_sizeunit_combobox.SetValue(self.FILESIZES[self.opt_manager.options["min_filesize_unit"]])
        self.filesize_max_sizeunit_combobox.SetValue(self.FILESIZES[self.opt_manager.options["max_filesize_unit"]])

        self._on_subtitles(None)

    def save_options(self):
        subs_choice = self.SUBS_CHOICES.index(self.subtitles_combobox.GetValue())
        if subs_choice == 1:
            self.opt_manager.options["write_subs"] = False
            self.opt_manager.options["write_all_subs"] = False
            self.opt_manager.options["write_auto_subs"] = True
        elif subs_choice == 2:
            self.opt_manager.options["write_subs"] = False
            self.opt_manager.options["write_all_subs"] = True
            self.opt_manager.options["write_auto_subs"] = False
        elif subs_choice == 3:
            self.opt_manager.options["write_subs"] = True
            self.opt_manager.options["write_all_subs"] = False
            self.opt_manager.options["write_auto_subs"] = False
        else:
            self.opt_manager.options["write_subs"] = False
            self.opt_manager.options["write_all_subs"] = False
            self.opt_manager.options["write_auto_subs"] = False

        self.opt_manager.options["subs_lang"] = tdict(self.SUBS_LANG)[self.subtitles_lang_listbox.GetStringSelection()]
        self.opt_manager.options["embed_subs"] = self.embed_subs_checkbox.GetValue()
        self.opt_manager.options["playlist_start"] = self.playlist_start_spinctrl.GetValue()
        self.opt_manager.options["playlist_end"] = self.playlist_stop_spinctrl.GetValue()
        self.opt_manager.options["max_downloads"] = self.playlist_max_spinctrl.GetValue()
        self.opt_manager.options["min_filesize"] = self.filesize_min_spinctrl.GetValue()
        self.opt_manager.options["max_filesize"] = self.filesize_max_spinctrl.GetValue()
        self.opt_manager.options["min_filesize_unit"] = tdict(self.FILESIZES)[self.filesize_min_sizeunit_combobox.GetValue()]
        self.opt_manager.options["max_filesize_unit"] = tdict(self.FILESIZES)[self.filesize_max_sizeunit_combobox.GetValue()]


class AdvancedTab(TabPanel):

    TEXTCTRL_SIZE = (300, -1)

    def __init__(self, *args, **kwargs):
        super(AdvancedTab, self).__init__(*args, **kwargs)

        self.retries_label = self.crt_statictext(("重试次数"))
        self.retries_spinctrl = self.crt_spinctrl((1, 999))

        self.auth_label = self.crt_statictext(("认证"))

        self.username_label = self.crt_statictext(("用户名"))
        self.username_textctrl = self.crt_textctrl()
        self.password_label = self.crt_statictext(("密码"))
        self.password_textctrl = self.crt_textctrl(wx.TE_PASSWORD)
        self.video_pass_label = self.crt_statictext(("视频密码"))
        self.video_pass_textctrl = self.crt_textctrl(wx.TE_PASSWORD)

        self.network_label = self.crt_statictext(("网络"))

        self.proxy_label = self.crt_statictext(("代理"))
        self.proxy_textctrl = self.crt_textctrl()
        self.useragent_label = self.crt_statictext(("User agent"))
        self.useragent_textctrl = self.crt_textctrl()
        self.referer_label = self.crt_statictext(("Referer"))
        self.referer_textctrl = self.crt_textctrl()

        self.logging_label = self.crt_statictext(("日志记录"))

        self.enable_log_checkbox = self.crt_checkbox(("启用日志"), self._on_enable_log)
        self.view_log_button = self.crt_button(("查看"), self._on_view)
        self.clear_log_button = self.crt_button(("清除"), self._on_clear)

        self._set_layout()

        if self.log_manager is None:
            self.view_log_button.Disable()
            self.clear_log_button.Disable()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        # Set up retries box
        retries_sizer = wx.BoxSizer(wx.HORIZONTAL)
        retries_sizer.Add(self.retries_label, flag=wx.ALIGN_CENTER_VERTICAL)
        retries_sizer.AddSpacer(20)
        retries_sizer.Add(self.retries_spinctrl)
        vertical_sizer.Add(retries_sizer, flag=wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT, border=5)

        # Set up authentication box
        vertical_sizer.Add(self.auth_label, flag=wx.TOP, border=10)
        auth_sizer = wx.GridBagSizer(5, -1)

        auth_sizer.Add(self.username_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.username_textctrl, (0, 2))

        auth_sizer.Add(self.password_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.password_textctrl, (1, 2))

        auth_sizer.Add(self.video_pass_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        auth_sizer.Add(self.video_pass_textctrl, (2, 2))

        auth_sizer.AddGrowableCol(1)
        vertical_sizer.Add(auth_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up network box
        vertical_sizer.Add(self.network_label, flag=wx.TOP, border=10)
        network_sizer = wx.GridBagSizer(5, -1)

        network_sizer.Add(self.proxy_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.proxy_textctrl, (0, 2))

        network_sizer.Add(self.useragent_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.useragent_textctrl, (1, 2))

        network_sizer.Add(self.referer_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        network_sizer.Add(self.referer_textctrl, (2, 2))

        network_sizer.AddGrowableCol(1)
        vertical_sizer.Add(network_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        # Set up logging box
        vertical_sizer.Add(self.logging_label, flag=wx.TOP, border=10)

        logging_sizer = wx.BoxSizer(wx.HORIZONTAL)
        logging_sizer.Add(self.enable_log_checkbox)
        logging_sizer.AddSpacer(1)
        logging_sizer.Add(self.view_log_button)
        logging_sizer.AddSpacer(5)
        logging_sizer.Add(self.clear_log_button)

        vertical_sizer.Add(logging_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def _on_enable_log(self, event):
        """Event handler for the wx.EVT_CHECKBOX of the enable_log_checkbox."""
        wx.MessageBox(("In order for the changes to take effect please restart {0}").format(__appname__),
                      ("Restart"),
                      wx.OK | wx.ICON_INFORMATION,
                      self)

    def _on_view(self, event):
        """Event handler for the wx.EVT_BUTTON of the view_log_button."""
        log_window = LogGUI(self)
        log_window.load(self.log_manager.log_file)
        log_window.Show()

    def _on_clear(self, event):
        """Event handler for the wx.EVT_BUTTON of the clear_log_button."""
        if self.log_manager is not None:
            self.log_manager.clear()

    def load_options(self):
        self.retries_spinctrl.SetValue(self.opt_manager.options["retries"])
        self.username_textctrl.SetValue(self.opt_manager.options["username"])
        self.password_textctrl.SetValue(self.opt_manager.options["password"])
        self.video_pass_textctrl.SetValue(self.opt_manager.options["video_password"])
        self.proxy_textctrl.SetValue(self.opt_manager.options["proxy"])
        self.useragent_textctrl.SetValue(self.opt_manager.options["user_agent"])
        self.referer_textctrl.SetValue(self.opt_manager.options["referer"])
        self.enable_log_checkbox.SetValue(self.opt_manager.options["enable_log"])

    def save_options(self):
        self.opt_manager.options["retries"] = self.retries_spinctrl.GetValue()
        self.opt_manager.options["username"] = self.username_textctrl.GetValue()
        self.opt_manager.options["password"] = self.password_textctrl.GetValue()
        self.opt_manager.options["video_password"] = self.video_pass_textctrl.GetValue()
        self.opt_manager.options["proxy"] = self.proxy_textctrl.GetValue()
        self.opt_manager.options["user_agent"] = self.useragent_textctrl.GetValue()
        self.opt_manager.options["referer"] = self.referer_textctrl.GetValue()
        self.opt_manager.options["enable_log"] = self.enable_log_checkbox.GetValue()


class ExtraTab(TabPanel):

    def __init__(self, *args, **kwargs):
        super(ExtraTab, self).__init__(*args, **kwargs)

        self.cmdline_args_label = self.crt_statictext(("Youtube-dl 命令行选项（例如：--help）"))
        self.cmdline_args_textctrl = self.crt_textctrl(wx.TE_MULTILINE | wx.TE_WORDWRAP)

        self.extra_opts_label = self.crt_statictext(("额外选项"))

        self.youtube_dl_debug_checkbox = self.crt_checkbox(("开启 Youtube-dl 调试模式"))
        self.ignore_errors_checkbox = self.crt_checkbox(("忽略错误"))
        self.ignore_config_checkbox = self.crt_checkbox(("忽略 Youtube-dl 配置文件"))
        self.no_mtime_checkbox = self.crt_checkbox(("不使用 mtime"))
        self.native_hls_checkbox = self.crt_checkbox(("优先使用原生 HLS"))

        self._set_layout()

    def _set_layout(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)

        vertical_sizer.Add(self.cmdline_args_label)
        vertical_sizer.Add(self.cmdline_args_textctrl, 1, wx.EXPAND | wx.ALL, border=5)

        vertical_sizer.Add(self.extra_opts_label, flag=wx.TOP, border=5)

        extra_opts_sizer = wx.WrapSizer()
        extra_opts_sizer.Add(self.youtube_dl_debug_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.ignore_errors_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.ignore_config_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.no_mtime_checkbox)
        extra_opts_sizer.AddSpacer(5)
        extra_opts_sizer.Add(self.native_hls_checkbox)

        vertical_sizer.Add(extra_opts_sizer, flag=wx.ALL, border=5)

        main_sizer.Add(vertical_sizer, 1, wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(main_sizer)

    def load_options(self):
        self.cmdline_args_textctrl.SetValue(self.opt_manager.options["cmd_args"])
        self.ignore_errors_checkbox.SetValue(self.opt_manager.options["ignore_errors"])
        self.youtube_dl_debug_checkbox.SetValue(self.opt_manager.options["youtube_dl_debug"])
        self.ignore_config_checkbox.SetValue(self.opt_manager.options["ignore_config"])
        self.native_hls_checkbox.SetValue(self.opt_manager.options["native_hls"])
        self.no_mtime_checkbox.SetValue(self.opt_manager.options["nomtime"])

    def save_options(self):
        self.opt_manager.options["cmd_args"] = self.cmdline_args_textctrl.GetValue()
        self.opt_manager.options["ignore_errors"] = self.ignore_errors_checkbox.GetValue()
        self.opt_manager.options["youtube_dl_debug"] = self.youtube_dl_debug_checkbox.GetValue()
        self.opt_manager.options["ignore_config"] = self.ignore_config_checkbox.GetValue()
        self.opt_manager.options["native_hls"] = self.native_hls_checkbox.GetValue()
        self.opt_manager.options["nomtime"] = self.no_mtime_checkbox.GetValue()


class LogGUI(wx.Frame):

    """Simple window for reading the STDERR.

    Attributes:
        TITLE (string): Frame title.
        FRAME_SIZE (tuple): Tuple that holds the frame size (width, height).

    Args:
        parent (wx.Window): Frame parent.

    """

    # REFACTOR move it on widgets module

    TITLE = ("Log Viewer")
    FRAME_SIZE = (750, 200)

    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent, title=self.TITLE, size=self.FRAME_SIZE)

        panel = wx.Panel(self)

        self._text_area = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )

        sizer = wx.BoxSizer()
        sizer.Add(self._text_area, 1, wx.EXPAND)
        panel.SetSizerAndFit(sizer)

    def load(self, filename):
        """Load file content on the text area. """
        if os_path_exists(filename):
            self._text_area.LoadFile(filename)
