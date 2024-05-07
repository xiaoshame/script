import wx
from crypt_page import AlgorithmPage
from time_page import TimePage
from pdf_page import PdfPage
from rates_page import RatesPage
from download_page import DownloadPage
from logmanager import LogManager
from optionsmanager import OptionsManager
from utils import (
    get_config_path,
    get_icon_file,
)

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None, title="常用工具", size=(820, 500))        
        config_path = get_config_path()
        self.opt_manager = OptionsManager(config_path)
        self.log_manager = None

        if self.opt_manager.options['enable_log']:
            self.log_manager = LogManager(config_path, self.opt_manager.options['log_time'])
        self.initUI()

    def initUI(self):
        # Set the app icon
        app_icon_path = get_icon_file()
        if app_icon_path is not None:
            self.app_icon = wx.Icon(app_icon_path, wx.BITMAP_TYPE_ICO)
            self.SetIcon(self.app_icon)
        self._status_bar = self.CreateStatusBar()
        self.panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.panel)
        self.algorithm_table = AlgorithmPage(self.notebook)
        self.time_table = TimePage(self.notebook)
        self.pdf_table = PdfPage(self.notebook)
        self.rates_table = RatesPage(self.notebook)
        self.download_table = DownloadPage(self.notebook,self.opt_manager,self.log_manager,self._status_bar)

        self.notebook.AddPage(self.download_table, "下载")
        self.notebook.AddPage(self.algorithm_table, "加解密")
        self.notebook.AddPage(self.time_table, "时间戳")
        self.notebook.AddPage(self.pdf_table, "PDF")
        self.notebook.AddPage(self.rates_table, "汇率")

        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)
        self.Show()

if __name__ == "__main__":
    app = wx.App()
    frame = MainWindow()
    app.MainLoop()