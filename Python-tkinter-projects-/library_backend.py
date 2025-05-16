 #---------- library_backend.py ----------
import logging
import sys
from datetime import datetime, timedelta
from collections import deque, defaultdict
import difflib

# ======= Logging Configuration =======
def configure_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# ========== Custom Exceptions ==========
class BookNotFoundError(Exception): pass
class BookNotAvailableError(Exception): pass
class UserLimitExceededError(Exception): pass
class ReservationError(Exception): pass

# ========== Domain Classes ==========
class Book:
    def __init__(self, title: str, author: str, isbn: str, genre: str, total_copies: int = 1):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.genre = genre
        self.total_copies = total_copies
        self.available_copies = total_copies

    def __repr__(self):
        return f"{self.title} by {self.author} (ISBN: {self.isbn}) - {self.available_copies}/{self.total_copies} available"

class eBook(Book):
    def __init__(self, title, author, isbn, genre, download_size_mb):
        super().__init__(title, author, isbn, genre, total_copies=1)
        self.download_size_mb = download_size_mb

# ========== Library Classes ==========
class Library:
    def __init__(self):
        self._books = {}
        self._reservations = defaultdict(deque)

    def add_book(self, book: Book, count: int = 1):
        if book.isbn in self._books:
            existing = self._books[book.isbn]
            existing.total_copies += count
            existing.available_copies += count
        else:
            book.total_copies = count
            book.available_copies = count
            self._books[book.isbn] = book
        logging.info(f"ADD_BOOK: {book.title} x{count}")

    def remove_book(self, isbn: str, count: int = 1):
        if isbn not in self._books:
            raise BookNotFoundError("Book not found in library")
        book = self._books[isbn]
        if count > book.available_copies:
            raise BookNotAvailableError("Cannot remove more copies than available")
        book.total_copies -= count
        book.available_copies -= count
        if book.total_copies <= 0:
            del self._books[isbn]
        logging.info(f"REMOVE_BOOK: {isbn} x{count}")

    def lend_book(self, isbn, user_id):
        if isbn not in self._books:
            raise BookNotFoundError("Book not found in library")
        book = self._books[isbn]
        if book.available_copies <= 0:
            raise BookNotAvailableError("Book currently not available")
        book.available_copies -= 1
        due = datetime.now() + timedelta(days=14)
        logging.info(f"LEND_BOOK: {isbn} to {user_id}, due {due.date()}")
        return due

    def return_book(self, isbn, user_obj, return_date=None):
        if isbn not in self._books:
            raise BookNotFoundError("Book not found in library")
        book = self._books[isbn]
        book.available_copies += 1
        if return_date:
            due = user_obj.borrowed_books.get(isbn)
            if due and return_date.date() > due.date():
                days_late = (return_date.date() - due.date()).days
                fine = days_late * 1
                print(f"You have a fine of ${fine} for late return.")
        if self._reservations[isbn]:
            next_user = self._reservations[isbn].popleft()
            print(f"Notification: {next_user}, your reserved book '{book.title}' is now available.")
            logging.info(f"RESERVATION_NOTIFY: {isbn} to {next_user}")
        logging.info(f"RETURN_BOOK: {isbn} by {user_obj.user_id}")

    def __iter__(self):
        self._iter_list = [b for b in self._books.values() if b.available_copies > 0]
        self._idx = 0
        return self

    def __next__(self):
        if self._idx >= len(self._iter_list):
            raise StopIteration
        book = self._iter_list[self._idx]
        self._idx += 1
        return book

    def search_by_title(self, title):
        matches = [b for b in self._books.values() if title.lower() in b.title.lower()]
        if matches:
            return matches
        titles = [b.title for b in self._books.values()]
        return difflib.get_close_matches(title, titles)

    def search_by_author(self, author):
        return [b for b in self._books.values() if author.lower() in b.author.lower()]

    def search_by_isbn(self, isbn):
        return self._books.get(isbn)

    def filter_by_genre(self):
        genres = defaultdict(list)
        for b in self._books.values():
            if b.available_copies > 0:
                genres[b.genre].append(b)
        return genres

    def reserve_book(self, isbn, user_id):
        if isbn not in self._books:
            raise BookNotFoundError("Book not found in library")
        if self._books[isbn].available_copies > 0:
            raise ReservationError("Book is available; no need to reserve")
        self._reservations[isbn].append(user_id)
        logging.info(f"RESERVE_BOOK: {isbn} by {user_id}")

class DigitalLibrary(Library):
    def add_ebook(self, ebook: eBook):
        self.add_book(ebook, count=1)
        logging.info(f"ADD_EBOOK: {ebook.title}")

# ========== User Management ==========
class User:
    def __init__(self, user_id, name, password):
        self.user_id = user_id
        self.name = name
        self._password = password
        self.borrowed_books = {}
        self.reserved_books = set()

    def verify_password(self, pw):
        return pw == self._password

class LibrarySystem:
    def __init__(self):
        configure_logging()
        self.library = Library()
        self.dlibrary = DigitalLibrary()
        self.users = {}
        self.current_user = None
        self.seed_library()

    def register_user(self, user_id, name, password):
        if user_id in self.users:
            print("User ID already exists.")
            return
        self.users[user_id] = User(user_id, name, password)
        print(f"User '{name}' registered successfully.")

    def login(self, user_id, password):
        user = self.users.get(user_id)
        if not user or not user.verify_password(password):
            print("Invalid credentials.")
            return False
        self.current_user = user
        print(f"Welcome, {user.name}!")
        return True

    def logout(self):
        self.current_user = None

    def list_books(self): return list(self.library)
    def add_book(self, book, count): return self.library.add_book(book, count)
    def lend_book(self, isbn): return self.library.lend_book(isbn, self.current_user.user_id)
    def return_book(self, isbn): return self.library.return_book(isbn, self.current_user, return_date=datetime.now())
    def search_books(self, by, term):
        if by == 'title': return self.library.search_by_title(term)
        if by == 'author': return self.library.search_by_author(term)
        if by == 'isbn': return [self.library.search_by_isbn(term)] if self.library.search_by_isbn(term) else []
    def reserve_book(self, isbn): return self.library.reserve_book(isbn, self.current_user.user_id)
    def filter_by_genre(self): return self.library.filter_by_genre()

    def seed_library(self):
        books_data = [
            ("To Kill a Mockingbird", "Harper Lee", "9780061120084", "Classic Fiction"),
            ("1984", "George Orwell", "9780451524935", "Dystopian Fiction"),
            ("Pride and Prejudice", "Jane Austen", "9780141199078", "Classic Romance"),
            ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", "Classic Fiction"),
            ("Moby-Dick", "Herman Melville", "9781503280786", "Adventure Fiction"),
            ("War and Peace", "Leo Tolstoy", "9780199232765", "Historical Fiction"),
            ("The Catcher in the Rye", "J.D. Salinger", "9780316769488", "Literary Fiction"),
            ("The Hobbit", "J.R.R. Tolkien", "9780547928227", "Fantasy"),
            ("Fahrenheit 451", "Ray Bradbury", "9781451673319", "Dystopian Fiction"),
            ("Brave New World", "Aldous Huxley", "9780060850524", "Dystopian Fiction"),
        ]
        for title, author, isbn, genre in books_data:
            b = Book(title, author, isbn, genre)
            self.library.add_book(b)