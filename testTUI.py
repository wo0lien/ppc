from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys

class ListView(Frame):
    def __init__(self, screen):
        super(ListView, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       on_load=self._reload_list,
                                       hover_focus=True,
                                       can_scroll=False,
                                       title="Deck")

        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,[("first option",1),("Second option", 2)],
            name="test",
            on_select=self._edit)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        pass

    def _reload_list(self, new_value=None):
        pass

    def _add(self):
        pass

    def _edit(self):
        pass

    def _delete(self):
        pass

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

def demo(screen):
    scenes = [
        Scene([ListView(screen)], -1, name="Main"),
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scenes[0], allow_int=True)

Screen.wrapper(demo, catch_interrupt=True)
sys.exit(0)