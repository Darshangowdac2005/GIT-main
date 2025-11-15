# frontend/views/home_view.py

import flet as ft
from frontend.api_client import get_items
from frontend.components.item_card import ItemCard

class HomeView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=20)
        self.page = page
        
        self.search_field = ft.TextField(label="Search by keyword or location", width=500)
        self.items_list = ft.ListView(expand=True, spacing=10)
        self.status_filter = ft.Dropdown(
            label="Filter Status",
            width=200,
            options=[
                ft.dropdown.Option("all", "All Listings"),
                ft.dropdown.Option("lost", "Lost Items"),
                ft.dropdown.Option("found", "Found Items"),
            ],
            value="all",
            on_change=self._load_items
        )
        
        self.content = self._build_ui()
        # Initial load
        self._load_items(None)

        # Subscribe to global pubsub to refresh when admin resolves claims or other updates occur
        def _on_pubsub_message(msg):
            if msg == "refresh_items":
                self._load_items(None)
        self.page.pubsub.subscribe(_on_pubsub_message)

    def _load_items(self, e):
        self.items_list.controls.clear()

        status = self.status_filter.value if self.status_filter.value != 'all' else None
        search = self.search_field.value.strip() if self.search_field.value else None

        # Display loading spinner while fetching
        self.items_list.controls.append(ft.Container(ft.ProgressRing(), alignment=ft.alignment.center))
        if self.page:
            self.page.update()

        all_items = get_items(status=status, search=search, include_resolved=True)
        self.items_list.controls.clear()

        if not all_items:
            self.items_list.controls.append(ft.Text("No items found. Report one!", size=16))
        else:
            # Separate resolved items for solved cases section
            unresolved_items = [item for item in all_items if item.get('status') != 'resolved']
            resolved_items = [item for item in all_items if item.get('status') == 'resolved']

            for item in unresolved_items:
                self.items_list.controls.append(ItemCard(item, self.page))

            if resolved_items:
                self.items_list.controls.append(ft.Divider(height=20))
                self.items_list.controls.append(ft.Text("Solved Cases", size=20))
                for item in resolved_items:
                    self.items_list.controls.append(ItemCard(item, self.page))

        if self.page:
            self.page.update()

    def _build_ui(self):
        return ft.Column(
            [
                ft.Row(
                    [
                        self.search_field,
                        ft.ElevatedButton(text="Search", icon=ft.icons.SEARCH, on_click=self._load_items),
                        self.status_filter
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    wrap=True
                ),
                ft.Divider(height=10),
                ft.Text("Recent Listings (Unresolved)", size=20),
                self.items_list
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )