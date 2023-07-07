环境：
python所有环境在requirements.txt里
主要用到以下库
PyQt5==5.12.3
SimpleITK==2.0.1
VTK @ file:///C:/Users/A/Anaconda3/Scripts/VTK-9.0.1-cp37-cp37m-win_amd64.whl

vtk 可在https://www.lfd.uci.edu/~gohlke/pythonlibs/#vtk    找到对应whl
使用pip install VTK-9.0.1-cp37-cp37m-win_amd64.whl 加载轮子

gui用qt设计，显示用vtk

data里存储nii或者nii.gz文件
image里存储ui.py需要的图标
ui.py实现nii和nii.gz文件的读取显示


现有功能如下：
打开文件并显示粗糙模型
打开filter开关可以显示高斯滤波后的模型，还可以显示整个读取空间的外接矩形（模型只占读取空间的一小部分）

tip：程序运行可能有点慢
