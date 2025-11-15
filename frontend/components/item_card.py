# frontend/components/item_card.py

import flet as ft
from frontend.api_client import claim_item_api

class ItemCard(ft.Card):
    def __init__(self, item_data, page):
        super().__init__(elevation=3, width=600)
        self.item = item_data
        self.page = page
        self.verification_field = ft.TextField(label="Verification Details", multiline=True, max_lines=3)
        self.content = self._build_content()

    def _show_claim_dialog(self, e):
        def close_dialog(e):
            self.page.dialog.open = False
            self.page.update()

        def submit_claim(e):
            details = self.verification_field.value.strip()
            if not details:
                self.page.show_snack_bar(ft.SnackBar(ft.Text("Please provide verification details.")))
                self.page.update()
                return
            result = claim_item_api(self.item['item_id'], details)
            if 'error' in result:
                self.page.show_snack_bar(ft.SnackBar(ft.Text(f"Claim failed: {result['error']}")))
            else:
                self.page.show_snack_bar(ft.SnackBar(ft.Text("Claim submitted successfully!")))
            self.page.update()
            close_dialog(e)

        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("File Claim"),
            content=ft.Column([
                ft.Text(f"Claiming: {self.item['title']}"),
                self.verification_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Submit", on_click=submit_claim),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog.open = True
        self.page.update()
    
    def _build_content(self):
        status_value = (self.item.get('status') or '').lower()
        status_color = ft.colors.GREEN_700 if status_value == 'found' else ft.colors.RED_700

        actions = []
        if status_value != 'resolved':
            actions.append(ft.ElevatedButton("File Claim", on_click=self._show_claim_dialog))
        row = ft.Row([
            ft.Text(f"Reported by: {self.item.get('reporter_name', 'Unknown')}", size=12, italic=True),
        ] + actions, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        return ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Row([
                        ft.Text(self.item.get('title', 'Untitled'), weight=ft.FontWeight.BOLD, size=18),
                        ft.Container(
                            content=ft.Text((status_value or '').upper(), color=ft.colors.WHITE, size=12),
                            bgcolor=status_color,
                            padding=ft.padding.only(left=8, right=8, top=2, bottom=2),
                            border_radius=5
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"Category: {self.item.get('category_name', 'N/A')}"),
                    ft.Text(((self.item.get('description') or '')[:100]) + ('...' if len(self.item.get('description') or '') > 100 else '')),
                    ft.Divider(),
                    row
                ]
            )
        )
