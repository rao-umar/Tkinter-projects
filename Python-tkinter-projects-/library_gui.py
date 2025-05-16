# ---------- library_gui.py ----------
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from library_backend import LibrarySystem, Book
from datetime import datetime

class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📚 My Library System")
        self.geometry("800x600")
        self.configure(bg="#ECEFF1")
        self.resizable(False, False)

        # Load custom theme
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        style.configure('Accent.TButton', background='#5C6BC0', foreground='white', font=(None, 10, 'bold'))
        style.map('Accent.TButton', background=[('active', '#3949AB')])
        style.configure('Header.TLabel', font=(None, 22, 'bold'), background='#ECEFF1')
        style.configure('TNotebook.Tab', padding=[12, 8], font=(None, 11, 'bold'))

        self.system = LibrarySystem()
        self.current_content = None
        self._build_welcome()

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _build_welcome(self):
        self._clear()
        # Center card
        card = ttk.Frame(self, style='Card.TFrame', padding=20)
        card.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        notebook = ttk.Notebook(card)
        notebook.pack(expand=True, fill='both')
        # Login Tab
        login_tab = ttk.Frame(notebook, padding=20, style='Card.TFrame')
        notebook.add(login_tab, text='Login')
        ttk.Label(login_tab, text='Welcome Back!', style='Header.TLabel').pack(pady=(0,15))
        self._make_input(login_tab, 'User ID')
        self.user_entry = ttk.Entry(login_tab, width=30)
        self.user_entry.pack(pady=5)
        self._make_input(login_tab, 'Password')
        self.pw_entry = ttk.Entry(login_tab, show='*', width=30)
        self.pw_entry.pack(pady=5)
        ttk.Button(login_tab, text='Login', style='Accent.TButton', command=self._on_login).pack(pady=15, ipady=4, fill='x')
        # Register Tab
        reg_tab = ttk.Frame(notebook, padding=20, style='Card.TFrame')
        notebook.add(reg_tab, text='Register')
        ttk.Label(reg_tab, text='Create Account', style='Header.TLabel').pack(pady=(0,15))
        self._make_input(reg_tab, 'User ID')
        self.reg_user = ttk.Entry(reg_tab, width=30)
        self.reg_user.pack(pady=5)
        self._make_input(reg_tab, 'Name')
        self.reg_name = ttk.Entry(reg_tab, width=30)
        self.reg_name.pack(pady=5)
        self._make_input(reg_tab, 'Password')
        self.reg_pw = ttk.Entry(reg_tab, show='*', width=30)
        self.reg_pw.pack(pady=5)
        ttk.Button(reg_tab, text='Register', style='Accent.TButton', command=self._on_register).pack(pady=15, ipady=4, fill='x')

    def _make_input(self, parent, label):
        ttk.Label(parent, text=label, background='#ECEFF1', font=(None, 10, 'bold')).pack(anchor=tk.W, pady=(10,0))

    def _on_login(self):
        if self.system.login(self.user_entry.get(), self.pw_entry.get()):
            self._build_main()
        else:
            messagebox.showerror('Login Failed', 'Invalid credentials.')

    def _on_register(self):
        uid, name, pw = self.reg_user.get(), self.reg_name.get(), self.reg_pw.get()
        if not uid or not name or not pw:
            messagebox.showwarning('Incomplete', 'All fields are required.')
            return
        self.system.register_user(uid, name, pw)
        messagebox.showinfo('Registered', 'Account created! Please switch to Login.')

    def _build_main(self):
        self._clear()
        # Top bar
        top = ttk.Frame(self, padding=10, style='Card.TFrame')
        top.pack(fill='x')
        ttk.Label(top, text=f'👤 {self.system.current_user.name}', font=(None,12), background='white').pack(side='left')
        ttk.Button(top, text='Logout', style='Accent.TButton', command=lambda: [self.system.logout(), self._build_welcome()]).pack(side='right')
        # Side menu
        menu = ttk.Frame(self, padding=10, style='Card.TFrame')
        menu.pack(side='left', fill='y')
        actions = [
            ('List All Books', self._list_books),
            ('Add New Book', self._add_book),
            ('Lend Book', self._lend_book),
            ('Return Book', self._return_book),
            ('Search Book', self._search_book),
            ('Reserve Book', self._reserve_book),
            ('Filter by Genre', self._filter_genre)
        ]
        for text, cmd in actions:
            ttk.Button(menu, text=text, style='Accent.TButton', command=cmd).pack(fill='x', pady=5)
        # Content
        self.content_frame = ttk.Frame(self, padding=10)
        self.content_frame.pack(side='right', expand=True, fill='both')
        self._list_books()

    def _update_content(self, widget):
        if self.current_content: self.current_content.destroy()
        self.current_content = widget
        widget.pack(expand=True, fill='both')

    # ==== Integrate backend operations ==== #
    def _list_books(self):
        frame = ttk.Frame(self.content_frame)
        for b in self.system.list_books():
            ttk.Label(frame, text=str(b)).pack(anchor='w')
        self._update_content(frame)

    def _add_book(self):
        d = AddBookDialog(self)
        self.wait_window(d)
        if d.result:
            title, author, isbn, genre, copies = d.result
            b = Book(title, author, isbn, genre, total_copies=int(copies))
            self.system.add_book(b, int(copies))
            messagebox.showinfo('Added', 'Book added successfully.')
            self._list_books()

    def _lend_book(self):
        isbn = simpledialog.askstring('Lend', 'ISBN:')
        try:
            due = self.system.lend_book(isbn)
            messagebox.showinfo('Lent', f'Due on {due.date()}')
            self._list_books()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _return_book(self):
        isbn = simpledialog.askstring('Return', 'ISBN:')
        try:
            self.system.return_book(isbn)
            messagebox.showinfo('Returned', 'Book returned successfully.')
            self._list_books()
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _search_book(self):
        by = simpledialog.askstring('Search', 'By (title/author/isbn):')
        term = simpledialog.askstring('Search', 'Term:')
        results = self.system.search_books(by, term)
        frame = ttk.Frame(self.content_frame)
        for b in results:
            ttk.Label(frame, text=str(b)).pack(anchor='w')
        self._update_content(frame)

    def _reserve_book(self):
        isbn = simpledialog.askstring('Reserve', 'ISBN:')
        try:
            self.system.reserve_book(isbn)
            messagebox.showinfo('Reserved', 'Book reserved.')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def _filter_genre(self):
        genres = self.system.filter_by_genre()
        frame = ttk.Frame(self.content_frame)
        for g, books in genres.items():
            ttk.Label(frame, text=f'{g}:', font=(None,12,'bold')).pack(anchor='w', pady=(10,0))
            for b in books:
                ttk.Label(frame, text=str(b)).pack(anchor='w')
        self._update_content(frame)

class AddBookDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Add New Book')
        self.configure(padx=20, pady=20, bg='#ECEFF1')
        self.result = None
        fields = ['Title','Author','ISBN','Genre','Copies']
        for f in fields:
            ttk.Label(self, text=f, font=(None,10,'bold'), background='#ECEFF1').pack(anchor='w', pady=(5,0))
            e = ttk.Entry(self, width=30)
            e.pack(pady=5)
            setattr(self, f.lower(), e)
        ttk.Button(self, text='OK', style='Accent.TButton', command=self._on_ok).pack(pady=10, fill='x')

    def _on_ok(self):
        self.result = [getattr(self, f.lower()).get() for f in ['title','author','isbn','genre','copies']]
        self.destroy()

if __name__ == '__main__':
    app = LibraryApp()
    app.mainloop()
# library_gui.py
# This file contains the GUI for the library system.