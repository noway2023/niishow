# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 16:32:18 2020

@author: phr
"""
import sys
import os
#sys.path.append("E:/Project/niishow")
sys.path.append(".")
import shutil
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor as QVTKWidget
from vtk.util.vtkImageImportFromArray import vtkImageImportFromArray
import SimpleITK as sitk
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore

__version__ = '2.0.0'
__author__ = 'phr'
__appname__ = 'NiiShow'


class PyPostMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(PyPostMainWindow, self).__init__()
        self.create_widgets()
        self.create_menu()
        self.load_settings()
        self.init_vtk_view()
        self.setWindowTitle('{} - v{}'.format(__appname__, __version__))

    def create_widgets(self):
        # 实例化一个QWidget，用作中心部件
        self.central_widget = QtWidgets.QWidget(self)
        self.central_widget.setObjectName('central_widget')

        # 设置QTabWidget
        self.tab_widget = QtWidgets.QTabWidget(self.central_widget)
        self.tab_widget.setObjectName("tab_widget")
        size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.tab_widget.sizePolicy().hasHeightForWidth())
        self.tab_widget.setSizePolicy(size_policy)

        # 创建result标签页
        self.set_result_tab()

        # 实例化一个QWidget，作为视图区的部件
        self.main_widget = QtWidgets.QWidget(self.central_widget)
        self.main_widget.setObjectName('main_widget')

        # 将中心部件的布局设置为垂直布局，将控件添加到布局中
        self.vertical_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.vertical_layout.setObjectName('vertical_layout')
        self.vertical_layout.addWidget(self.tab_widget)
        self.vertical_layout.addWidget(self.main_widget)
        self.setCentralWidget(self.central_widget)

    def set_result_tab(self):
        # 创建result标签页
        self.result_tab = QtWidgets.QWidget()
        self.result_tab.setObjectName('result_tab')

        # 将标签页的布局设置为网格布局，以便有序添加其它控件
        self.result_grid_layout = QtWidgets.QGridLayout(self.result_tab)
        self.result_grid_layout.setObjectName('result_grid_layout')

        # 将后处理中变形相关的控件放置到一个水平布局中
        self.deformation_horizontal_layout = QtWidgets.QHBoxLayout()
        self.deformation_horizontal_layout.setObjectName('deformation_horizontal_layout')
        # 添加一个checkbox，用来决定是否显示变形
        self.deformation_check_box = QtWidgets.QCheckBox(self.result_tab)
        self.deformation_check_box.setObjectName('deformation_check_box')
        self.deformation_check_box.setText('filter')
        self.deformation_check_box.stateChanged.connect(self.draw_displacement)
        # 添加一个combobox，用来决定是否显示初始形状
        self.deformation_combo_box = QtWidgets.QComboBox(self.result_tab)
        self.deformation_combo_box.setObjectName('deformation_combo_box')
        self.deformation_combo_box.addItem('高斯滤波')
        self.deformation_combo_box.addItem('外接框+高斯滤波')
        self.deformation_combo_box.currentTextChanged.connect(self.draw_displacement)
        # 添加一个spaceritem，让控件向左边集中
        deformation_spacer_item = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.deformation_horizontal_layout.addWidget(self.deformation_check_box)
        self.deformation_horizontal_layout.addWidget(self.deformation_combo_box)
        self.deformation_horizontal_layout.addItem(deformation_spacer_item)

        # 将控件添加到网格布局中，再将标签页添加到QTabWidget中
        self.result_grid_layout.addLayout(self.deformation_horizontal_layout, 0, 1, 1, 1)
        self.tab_widget.addTab(self.result_tab, '结果')

    def create_menu(self):
        self.setup_file_menu()
        self.setup_view_menu()
        self.setup_help_menu()
        status = self.statusBar()
        status.setSizeGripEnabled(False)

    def create_action(self, text, slot=None, shortcut=None, icon=None,
                      tip=None, checkable=False, signal='triggered'):
        action = QtWidgets.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            getattr(action, signal).connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def setup_file_menu(self):
        file_menu = self.menuBar().addMenu('文件')
        file_toolbar = self.addToolBar('文件')
        file_toolbar.setObjectName('file_toolbar')
        file_open_action = self.create_action(
            '打开', self.file_open, QtGui.QKeySequence.Open,
            "image/open", '打开文件')
        file_quit_action = self.create_action(
            '退出', self.close, 'Ctrl+Q', "image/quit", '退出')
        self.add_actions(
            file_menu, (file_open_action, None, file_quit_action))
        self.add_actions(file_toolbar, (file_open_action, file_quit_action))

    def setup_view_menu(self):
        view_menu = self.menuBar().addMenu('视图')
        view_toolbar = self.addToolBar('视图')
        view_toolbar.setObjectName('view_toolbar')
        view_fit_action = self.create_action(
            '适合窗口', self.fit_all, 'Ctrl+F', "image/fit", '适合窗口')
        self.add_actions(view_menu, (view_fit_action, ))
        self.add_actions(view_toolbar, (view_fit_action,))

    def setup_help_menu(self):
        help_menu = self.menuBar().addMenu('帮助')
        help_action = self.create_action(
            "帮助", self.help, icon="image/help", tip='帮助')
        about_action = self.create_action(
            "关于", self.about, icon="image/about", tip='关于')
        self.add_actions(help_menu, (help_action, about_action))

    def about(self):
        QtWidgets.QMessageBox.about(
            self, self.tr('关于PyPost'),
            """<b>PyPost</b> v{} by {}""".format(__version__, __author__))

    def fit_all(self):
        self.renderer.ResetCamera()
        self.render_window.Render()

    # 重写关闭事件，重新打开可恢复上次关闭界面大小
    def closeEvent(self, event):
        settings = QtCore.QSettings()
        settings.setValue('./Geometry',
                          QtCore.QVariant(self.saveGeometry()))
        settings.setValue('./State',
                          QtCore.QVariant(self.saveState()))
        os.remove(self.filename)

    def load_settings(self):
        # 使用QSettings恢复上次关闭时的状态
        self.filename = None
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value(
            './Geometry', type=QtCore.QByteArray))
        self.restoreState(settings.value(
            './State', type=QtCore.QByteArray))

    def file_open(self):
        if self.filename:
            os.remove(self.filename)

        self.filename1, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, '打开文件 - nii文件', '.', '(*.nii *.nii.gz)')
        filename = os.path.basename(self.filename1)
        shutil.copy(self.filename1, os.getcwd())
        self.filename = os.getcwd() + '\\' + filename

        self.renderer.RemoveAllViewProps()

        if self.filename:
            self.deformation_check_box.setCheckState(0)
            ds = sitk.ReadImage(self.filename)
            data = sitk.GetArrayFromImage(ds)
            self.imgshape = data.shape
            self.imgshape = [self.imgshape[2], self.imgshape[1], self.imgshape[0]]
            spacing = ds.GetSpacing()
            srange = [np.min(data), np.max(data)]
            self.original_model = vtkImageImportFromArray()
            self.original_model.SetArray(data)
            self.original_model.SetDataSpacing(spacing)
            origin = (0, 0, 0)
            self.original_model.SetDataOrigin(origin)
            self.original_model.Update()
            min = srange[0]
            max = srange[1]
            diff = max - min
            inter = 4200 / diff
            shift = -min
            self.isovalue = 1150
            # 对偏移和比例参数来对图像数据进行操作 数据转换，之后直接调用shifter
            self.shifter = vtk.vtkImageShiftScale()
            self.shifter.SetShift(shift)
            self.shifter.SetScale(inter)
            self.shifter.SetOutputScalarTypeToUnsignedShort()
            self.shifter.SetInputData(self.original_model.GetOutput())
            self.shifter.ReleaseDataFlagOff()
            self.shifter.Update()

            self.locator = vtk.vtkMergePoints()
            self.locator.SetDivisions(self.imgshape)
            self.locator.SetNumberOfPointsPerBucket(2)
            self.locator.AutomaticOff()
            # 用MC方法提取iso
            self.iso = vtk.vtkMarchingCubes()
            self.iso.SetInputConnection(self.shifter.GetOutputPort())
            self.iso.ComputeGradientsOn()
            self.iso.ComputeScalarsOff()
            self.iso.ComputeNormalsOn()
            self.iso.SetValue(0, self.isovalue)
            # self.iso.SetValue(1, self.isovalue // 2)
            # self.iso.SetLocator(self.locator)

            self.isoMapper = vtk.vtkPolyDataMapper()
            self.isoMapper.SetInputConnection(self.iso.GetOutputPort())
            self.isoMapper.ScalarVisibilityOff()

            self.original_Actor = vtk.vtkActor()
            self.original_Actor.SetMapper(self.isoMapper)

            self.renderer.AddActor(self.original_Actor)
            self.renderer.SetBackground(0, 0, 0)
            # self.render_window.SetSize(self.main_widget.width, self.main_widget.height)
            self.renderer.ResetCamera()
            self.iren.Initialize()
            self.render_window.Render()
            self.iren.Start()
            self.gaussian_actor = None
            self.outline_actor = None

    def init_vtk_view(self):
        # 在之前创建的main_widget上添加vtk控件
        self.vtk_vertical_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.vtk_widget = QVTKWidget(self.main_widget)
        self.vtk_vertical_layout.addWidget(self.vtk_widget)

        self.render_window = self.vtk_widget.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1.0, 1.0, 1.0)
        self.render_window.AddRenderer(self.renderer)
        self.render_window.Render()
        self.iren = self.render_window.GetInteractor()
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.style)

    def draw_displacement(self):
        # 已经打开结果文件才执行
        if self.filename:
            show_displacement = self.deformation_check_box.isChecked()
            # 如果显示变形，则隐藏原始模型
            if show_displacement:
                self.original_Actor.VisibilityOff()
                if not self.gaussian_actor:
                    # 加入高斯滤波模块
                    gaussianRadius = 1
                    gaussianStandardDeviation = 2.0
                    self.gaussian = vtk.vtkImageGaussianSmooth()
                    self.gaussian.SetStandardDeviations(gaussianStandardDeviation, gaussianStandardDeviation, gaussianStandardDeviation)
                    self.gaussian.SetRadiusFactors(gaussianRadius, gaussianRadius, gaussianRadius)
                    self.gaussian.SetInputConnection(self.shifter.GetOutputPort())
                    # 用MC方法提取iso
                    self.guassianiso = vtk.vtkMarchingCubes()
                    self.guassianiso.SetInputConnection(self.gaussian.GetOutputPort())
                    self.guassianiso.ComputeGradientsOn()
                    self.guassianiso.ComputeScalarsOff()
                    self.guassianiso.ComputeNormalsOn()
                    self.guassianiso.SetValue(0, self.isovalue)
                    # self.guassianiso.SetValue(1, self.isovalue // 2)
                    # self.guassianiso.SetLocator(self.locator)

                    self.smoother = vtk.vtkWindowedSincPolyDataFilter()
                    self.smoother.SetInputConnection(self.guassianiso.GetOutputPort())
                    smoothingIterations = 5
                    passBand = 0.001
                    featureAngle = 60.0
                    self.smoother.SetNumberOfIterations(smoothingIterations)
                    self.smoother.BoundarySmoothingOff()
                    self.smoother.FeatureEdgeSmoothingOff()
                    self.smoother.SetFeatureAngle(featureAngle)
                    self.smoother.SetPassBand(passBand)
                    self.smoother.NonManifoldSmoothingOn()
                    self.smoother.NormalizeCoordinatesOn()
                    self.smoother.Update()

                    self.normals = vtk.vtkPolyDataNormals()
                    self.normals.SetInputConnection(self.smoother.GetOutputPort())
                    self.normals.SetFeatureAngle(featureAngle)

                    self.stripper = vtk.vtkStripper()
                    self.stripper.SetInputConnection(self.normals.GetOutputPort())

                    self.deformation_mapper = vtk.vtkPolyDataMapper()
                    self.deformation_mapper.SetInputConnection(self.stripper.GetOutputPort())
                    self.deformation_mapper.ScalarVisibilityOff()

                    self.gaussian_actor = vtk.vtkActor()
                    self.gaussian_actor.SetMapper(self.deformation_mapper)

                    self.renderer.AddActor(self.gaussian_actor)

                if self.deformation_combo_box.currentText() == '高斯滤波':
                    if self.outline_actor:
                        self.outline_actor.VisibilityOff()
                    self.gaussian_actor.VisibilityOn()
                elif self.deformation_combo_box.currentText() == '外接框+高斯滤波':
                    self.gaussian_actor.VisibilityOn()
                    if self.outline_actor:
                        self.outline_actor.VisibilityOn()
                    else:
                        outline = vtk.vtkOutlineFilter()
                        outline.SetInputConnection(self.original_model.GetOutputPort())
                        outline_mapper = vtk.vtkPolyDataMapper()
                        outline_mapper.SetInputConnection(outline.GetOutputPort())
                        self.outline_actor = vtk.vtkActor()
                        self.outline_actor.SetMapper(outline_mapper)
                        self.outline_actor.GetProperty().SetColor(1.0, 0.5, 0.5)

                        self.renderer.AddActor(self.outline_actor)
            # 不显示变形时，显示原始模型
            else:
                if self.gaussian_actor:
                    self.gaussian_actor.VisibilityOff()
                if self.outline_actor:
                    self.outline_actor.VisibilityOff()
                self.original_Actor.VisibilityOn()
            self.render_window.Render()

    def help(self):
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('{}'.format(__appname__))
    app.setOrganizationName('phr')

    QtCore.QCoreApplication.setOrganizationName("MySoft")
    QtCore.QCoreApplication.setOrganizationDomain("mysoft.com")
    QtCore.QCoreApplication.setApplicationName("VtkShow")

    win = PyPostMainWindow()
    win.show()
    app.exec_()
