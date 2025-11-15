# frontend/views/signup_view.py

import flet as ft
from frontend.api_client import signup_user

class SignupView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, alignment=ft.alignment.center)
        self.page = page
        
        self.name_field = ft.TextField(label="Name", width=300)
        self.email_field = ft.TextField(label="Email", width=300)
        self.password_field = ft.TextField(label="Password", password=True, width=300)
        self.confirm_password_field = ft.TextField(label="Confirm Password", password=True, width=300)
        self.role_choice = ft.Dropdown(
            label="Role",
            width=300,
            options=[
                ft.dropdown.Option("student", "Student"),
                ft.dropdown.Option("faculty", "Faculty"),
                ft.dropdown.Option("admin", "Admin")
            ],
            value="student"
        )
        self.message_text = ft.Text("")

        self.content = self._build_ui()

    def _handle_signup(self, e):
        name = self.name_field.value
        email = self.email_field.value
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        if not all([name, email, password, confirm_password]):
            self.message_text.value = "All fields are required."
            self.page.update()
            return
        
        if password != confirm_password:
            self.message_text.value = "Passwords do not match."
            self.page.update()
            return
        
        self.message_text.value = "Signing up..."
        self.page.update()
        
        role = self.role_choice.value
        result = signup_user(name, email, password, role)
        
        if result and 'message' in result:
            self.message_text.value = "Signup successful! Please login."
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Signup successful! Please login."),
                bgcolor=ft.colors.GREEN_400
            )
            self.page.snack_bar.open = True
            self.page.go("/login")
        else:
            self.message_text.value = result.get('error', 'Signup failed.')
            self.page.update()

    def _build_ui(self):
        return ft.Column(
            [
                ft.Card(
                    content=ft.Container(
                        ft.Column(
                            [
                                ft.Text("User Signup", size=24, weight=ft.FontWeight.BOLD),
                                self.name_field,
                                self.email_field,
                                self.password_field,
                                self.confirm_password_field,
                                self.role_choice,
                                ft.ElevatedButton(text="Sign Up", on_click=self._handle_signup),
                                self.message_text
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=20
                        ),
                        padding=30
                    ),
                    elevation=10,
                    width=400
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
