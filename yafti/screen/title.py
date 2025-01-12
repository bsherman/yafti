import asyncio
from functools import partial
from typing import Optional, List

from gi.repository import Adw, Gtk

from yafti.abc import YaftiScreen, YaftiScreenConfig
from yafti import events
from yafti.registry import PLUGINS

_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<interface>
    <requires lib="gtk" version="4.0"/>
    <requires lib="libadwaita" version="1.0" />
    <template class="YaftiTitleScreen" parent="AdwBin">
        <property name="halign">fill</property>
        <property name="valign">fill</property>
        <property name="hexpand">true</property>
        <child>
            <object class="AdwStatusPage" id="status_page">
                <property name="icon-name">folder</property>
                <property name="title" translatable="yes">Welcome!</property>
                <property name="description" translatable="yes">
                    Make your choices, this wizard will take care of everything.
                </property>
            </object>
        </child>
    </template>
</interface>
"""


@Gtk.Template(string=_xml)
class TitleScreen(YaftiScreen, Adw.Bin):
    __gtype_name__ = "YaftiTitleScreen"

    status_page = Gtk.Template.Child()

    class Config(YaftiScreenConfig):
        title: str
        description: str
        icon: Optional[str] = None
        links: List[dict[str, dict]] = None

    def __init__(
        self,
        title: str = None,
        description: str = None,
        icon: str = None,
        links: List[dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.status_page.set_title(title)
        self.status_page.set_description(description)

        if links:
            links_list_box = self.render_links_list_box()
            self.append_action_rows(links, links_list_box)

    def render_links_list_box(self):
        links_list_box = Gtk.ListBox()
        links_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        links_list_box.add_css_class("boxed-list")
        self.status_page.set_child(links_list_box)
        return links_list_box

    def append_action_rows(self, links, links_list_box):
        for link in links:
            title, action = list(link.items())[0]
            plugin, config = list(action.items())[0]
            events.register("on_action_row_open")

            events.on(
                "on_action_row_open", lambda _: self.on_action_row_open(plugin, config)
            )

            def do_emit(*args, **kwargs):
                asyncio.create_task(events.emit(*args, **kwargs))

            _on_clicked = partial(do_emit, "on_action_row_open")

            link_action_row = Adw.ActionRow()

            action_btn = Gtk.Button()
            action_btn.set_label("Open")
            action_btn.set_valign(Gtk.Align.CENTER)
            action_btn.connect("clicked", _on_clicked)

            link_action_row.set_title(title)
            link_action_row.add_suffix(action_btn)

            links_list_box.append(link_action_row)

    async def on_action_row_open(self, plugin, config):
        await PLUGINS.get(plugin)(config)
