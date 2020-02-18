封装Control
============

QT4C中提供了丰富的控件类型供使用，如ListView， TrayNotifyBar, ComboBox等，对于Win32控件和UIA控件，QT4C封装了不同的控件类型可供使用，QT4C在Python层也对这些控件的自动化做了封装，以供使用。

QT4C已支持的一些常用控件类型如下（对于未封装的控件类型应使用Control基类进行封装）：

Win32控件：

=========================     ==============================    ====================================================   
控件类型                        使用场景                           对应接口                                                           
=========================     ==============================    ====================================================
输入框                          常用于一般的输入框                  :class:`qt4c.wincontrols.TextBox`             
下拉框                          可获取/选择下拉选项中某项            :class:`qt4c.wincontrols.ComboBox`          
列表(项)                        常用于一般的列表                    :class:`qt4c.wincontrols.ListView`    
菜单(项)                        可获取菜单项                        :class:`qt4c.wincontrols.Menu`           
树列表(项)                      树形控件，如文件列表树               :class:`qt4c.wincontrols.TreeView`                                                   
=========================     ==============================    ====================================================  

UIA控件：

=========================     ==============================    ==================================================== 
控件类型                        使用场景                           对应接口                                           
=========================     ==============================    ==================================================== 
输入框                          可进行输入操作                     :class:`qt4c.uiacontrols.Edit`                                                          
下拉框                          可获取/选择下拉选项中某项           :class:`qt4c.uiacontrols.ComboBox`                                             
单选按钮                        可获取按钮状态                     :class:`qt4c.uiacontrols.RadioButton`  
=========================     ==============================    ==================================================== 


更多控件类型请参考《:ref:`qt4c_package`》进行使用。

参照《:ref:`ui_locator`》，一个简单的控件定义如下，这里封装了计算器主界面的按键1::

    class MainPanel(win.Window):
        def __init__(self, qpath=None):
            qp = QPath("/ClassName='CalcFrame' && Text='计算器' && Visible='True'")
            super(MainPanel, self).__init__(locator=qp)

            self.updateLocator({
                '按键1': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x83'")},
            })

你也可以使用封装好的控件类型作为基类进行封装（假设按键1是一个UIA按钮控件）::

    import qt4c.uiacontrols as uia
    self.updateLocator({
        '按键1': {'type': uia.Button, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x83'")},
    })

定义完成之后，在MainPanel的接口下调用方式如下::

    self.Controls['按键1']

我们还可以获取其属性，例如ControlId属性::

    print self.Controls['按键1'].ControlId

或者点击::

    self.Controls['按键1'].click()