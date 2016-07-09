# coding=utf-8
from pyglet.gl import *
import pyglet
from pyglet.window import key
import Tkinter
import tkFileDialog


def draw_rect(x, y, width, height):               # pyglet.openGL语句 画矩形的四个点
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()


class Control(pyglet.event.EventDispatcher):       # 控制事件eneric event dispatcher interface
    x = y = 0
    width = height = 10

    def __init__(self, parent):
        super(Control, self).__init__()
        self.parent = parent

    def hit_test(self, x, y):  # 点中控件
        return (self.x < x < self.x + self.width and
                self.y < y < self.y + self.height)

    def capture_events(self):      # 获取事件
        self.parent.push_handlers(self)

    def release_events(self):      # 释放事件
        self.parent.remove_handlers(self)


class Button(Control):    #  按钮与事件连接
    charged = False

    def draw(self):     # 画按钮
        if self.charged:     # 如果点击
            glColor3f(0, 1, 0)         # 设置按键颜色  绿色
        draw_rect(self.x, self.y, self.width, self.height)
        glColor3f(1, 1, 1)      # 白色
        self.draw_label()

    def on_mouse_press(self, x, y, button, modifiers):
        self.capture_events()    # 调度事件
        self.charged = True   # 鼠标点击 按键变化

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):   # 拖动
        self.charged = self.hit_test(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.release_events()
        if self.hit_test(x, y):
            self.dispatch_event('on_press')
        self.charged = False      # 释放鼠标，恢复事件

Button.register_event_type('on_press')  # 注册事件


class TextButton(Button):              # 书写按钮内容
    def __init__(self, *args, **kwargs):
        super(TextButton, self).__init__(*args, **kwargs)
        self._text = pyglet.text.Label('', anchor_x='center', anchor_y='center')

    def draw_label(self):        # 添加标签
        self._text.x = self.x + self.width / 2
        self._text.y = self.y + self.height / 2
        self._text.draw()

    def set_text(self, text):   # 改变按钮的文本                   改变按钮的位置和大小
        self._text.text = text

    text = property(lambda self: self._text.text,
                    set_text)


class Slider(Control):    # 滑块控制
    THUMB_WIDTH = 6
    THUMB_HEIGHT = 10                # 滑块高度
    GROOVE_HEIGHT = 2                # 进度条高度

    def draw(self):
        center_y = self.y + self.height / 2
        draw_rect(self.x, center_y - self.GROOVE_HEIGHT / 2,
                  self.width, self.GROOVE_HEIGHT)
        pos = self.x + self.value * self.width / (self.max - self.min)
        draw_rect(pos - self.THUMB_WIDTH / 2, center_y - self.THUMB_HEIGHT / 2,
                  self.THUMB_WIDTH, self.THUMB_HEIGHT)

    def coordinate_to_value(self, x):           # 改变进度
        return float(x - self.x) / self.width * (self.max - self.min) + self.min

    def on_mouse_press(self, x, y, button, modifiers):    # 点击鼠标
        value = self.coordinate_to_value(x)
        self.capture_events()
        self.dispatch_event('on_begin_scroll')
        self.dispatch_event('on_change', value)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):  # 拖动
        value = min(max(self.coordinate_to_value(x), self.min), self.max)
        self.dispatch_event('on_change', value)

    def on_mouse_release(self, x, y, button, modifiers):  # 释放
        self.release_events()
        self.dispatch_event('on_end_scroll')

Slider.register_event_type('on_begin_scroll')
Slider.register_event_type('on_end_scroll')
Slider.register_event_type('on_change')


class PlayerWindow(pyglet.window.Window):          # 主类   画面部分
    GUI_WIDTH = 400
    GUI_HEIGHT = 40
    GUI_PADDING = 4         # 按钮间隔
    GUI_BUTTON_HEIGHT = 16

    def __init__(self, player):
        super(PlayerWindow, self).__init__(caption='Media Player',
                                           visible=False,
                                           resizable=True)
        self.player = player
        self.player.push_handlers(self)          # 获取事件
        self.player.eos_action = self.player.EOS_PAUSE

        self.slider = Slider(self)                    # 设置滑块
        self.slider.x = self.GUI_PADDING           # 类变量
        self.slider.y = self.GUI_PADDING * 2 + self.GUI_BUTTON_HEIGHT       # 进度条高度相对于底端
        self.slider.on_begin_scroll = lambda: player.pause()
        self.slider.on_end_scroll = lambda: player.play()
        self.slider.on_change = lambda value: player.seek(value)

        self.open_button = TextButton(self)               # 设置打开按钮
        self.open_button.x = self.GUI_PADDING
        self.open_button.y = self.GUI_PADDING
        self.open_button.height = self.GUI_BUTTON_HEIGHT
        self.open_button.width = 45
        self.open_button.text = 'Open'
        self.open_button.on_press = self.on_open

        self.stop_button = TextButton(self)               # 设置停止按钮
        self.stop_button.x = self.GUI_PADDING + self.open_button.width + self.open_button.x
        self.stop_button.y = self.GUI_PADDING
        self.stop_button.height = self.GUI_BUTTON_HEIGHT
        self.stop_button.width = 45
        self.stop_button.text = 'Stop'
        self.stop_button.on_press = self.on_stop

        self.play_pause_button = TextButton(self)                    # 设置打开暂停按钮
        self.play_pause_button.x = self.stop_button.x + self.stop_button.width + self.GUI_PADDING
        self.play_pause_button.y = self.GUI_PADDING
        self.play_pause_button.height = self.GUI_BUTTON_HEIGHT
        self.play_pause_button.width = 50
        self.play_pause_button.text = 'Pause'
        self.play_pause_button.on_press = self.on_play_pause

        win = self                # 自有妙用
        self.window_button = TextButton(self)                     # 设置缩放按钮
        self.window_button.x = self.play_pause_button.x + self.play_pause_button.width + self.GUI_PADDING
        self.window_button.y = self.GUI_PADDING
        self.window_button.height = self.GUI_BUTTON_HEIGHT
        self.window_button.width = 100
        self.window_button.text = 'Windowed'
        self.window_button.on_press = lambda: win.set_fullscreen(False)       # 注意不能写self

        self.raise_button = TextButton(self)                      # 增加音量按钮
        self.raise_button.x = 500
        self.raise_button.y = self.GUI_PADDING
        self.raise_button.height = self.GUI_BUTTON_HEIGHT
        self.raise_button.width = 30
        self.raise_button.text = '+'
        self.raise_button.on_press = self.on_raise

        self.lower_button = TextButton(self)        # 减小音量按钮
        self.lower_button.x = self.GUI_PADDING + self.raise_button.x + self.raise_button.width
        self.lower_button.y = self.GUI_PADDING
        self.lower_button.height = self.GUI_BUTTON_HEIGHT
        self.lower_button.width = 30
        self.lower_button.text = '-'
        self.lower_button.on_press = self.on_lower

        self.controls = [               # 与后面的draw()搭配，画出每个按钮
            self.slider,
            self.play_pause_button,
            self.window_button,
            self.open_button,
            self.stop_button,
            self.raise_button,
            self.lower_button,
        ]

        x = self.window_button.x + self.window_button.width + self.GUI_PADDING
        i = 0
        for screen in self.display.get_screens():           # 全屏按钮
            screen_button = TextButton(self)
            screen_button.x = x
            screen_button.y = self.GUI_PADDING
            screen_button.height = self.GUI_BUTTON_HEIGHT
            screen_button.width = 80
            screen_button.text = 'Screen %d' % (i + 1)
            screen_button.on_press = \
                (lambda s: lambda: win.set_fullscreen(True, screen=s))(screen)
            self.controls.append(screen_button)
            i += 1
            x += screen_button.width + self.GUI_PADDING

    def on_eos(self):
        self.gui_update_state()

    def gui_update_source(self):        # 滑块部分的播放设置
        if self.player.source:          # 有播放资源时
            source = self.player.source
            self.slider.min = 0.
            self.slider.max = source.duration
        else:
            self.slider.min = 0.
            self.slider.max = 500
        self.gui_update_state()

    def gui_update_state(self):             # 刷新按键状态
        if self.player.playing:
            self.play_pause_button.text = 'Pause'
        else:
            self.play_pause_button.text = 'Play'

    def get_video_size(self):   # 获取视频的大小并设置播放器的长宽
        if not self.player.source or not self.player.source.video_format:    # 版式，格局
            return 0, 0
        video_format = self.player.source.video_format
        width = video_format.width
        height = video_format.height
        if video_format.sample_aspect > 1:
            width *= video_format.sample_aspect
        elif video_format.sample_aspect < 1:
            height /= video_format.sample_aspect
        return width, height

    def on_resize(self, width, height):         # 重新布局滑块窗口
        '''Position and size video image.'''
        super(PlayerWindow, self).on_resize(width, height)

        self.slider.width = width - self.GUI_PADDING * 2

        height -= self.GUI_HEIGHT
        if height <= 0:
            return

        video_width, video_height = self.get_video_size()
        if video_width == 0 or video_height == 0:
            return

        display_aspect = width / float(height)
        video_aspect = video_width / float(video_height)      # 长宽比
        if video_aspect > display_aspect:
            self.video_width = width
            self.video_height = width / video_aspect
        else:
            self.video_height = height
            self.video_width = height * video_aspect
        self.video_x = (width - self.video_width) / 2
        self.video_y = (height - self.video_height) / 2 + self.GUI_HEIGHT

    def on_mouse_press(self, x, y, button, modifiers):       # 鼠标输入。
        for control in self.controls:
            if control.hit_test(x, y):
                control.on_mouse_press(x, y, button, modifiers)

    def on_key_press(self, symbol, modifiers):        # 键盘输入，空格即暂停，esc即关闭
        if symbol == key.SPACE:
            self.on_play_pause()
        elif symbol == key.ESCAPE:
            self.dispatch_event('on_close')

    def on_open(self):               # 打开按钮设置  使用Tkinter内的函数调出打开界面
        tk = Tkinter.Tk()
        tk.withdraw()
        dlg = tkFileDialog.askopenfilename(title='Choose a media file',
                                           filetypes=[("All files", "*.*"), ("HTML files", "*.html;*.htm")])
        filename = str(dlg)
        tk.quit()
        self.on_stop()
        source1 = pyglet.media.load(filename)  # 读取文件
        player.queue(source1)
        window.set_visible(True)             # 显示图形界面
        player.play()
        window.gui_update_source()

    def on_stop(self):
        if self.player.playing:   # 播放时点击停止
            self.player.seek(0)        # 滑块归零
            self.player.next_source()    # 播放下一个资源

    def on_close(self):     # 关闭设置
        self.player.pause()
        self.close()

    def on_play_pause(self):
        if self.player.playing:
            self.player.pause()
        else:
            if self.player.time >= self.player.source.duration:  # 如果放完了
                self.player.seek(0)   # 返回开始。   可用作停止按钮
            self.player.play()
        self.gui_update_state()

    def on_raise(self):
        a = self.player.volume
        a += 0.1
        self.player.volume = a

    def on_lower(self):
        a = self.player.volume
        a -= 0.1
        self.player.volume = a

    def on_draw(self):       # 画出视频，各按键画面
        self.clear()

        # Video
        if self.player.source and self.player.source.video_format:
            self.player.get_texture().blit(self.video_x,
                                           self.video_y,
                                           width=self.video_width,
                                           height=self.video_height)

        # GUI
        self.slider.value = self.player.time
        for control in self.controls:
            control.draw()

if __name__ == '__main__':
    player = pyglet.media.Player()      # 调用Player类
    window = PlayerWindow(player)    # 生成图形界面window

    window.gui_update_source()

    window.set_visible(True)
    pyglet.app.run()

