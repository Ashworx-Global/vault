import { verseData } from '../data/verses';
import { bookChapters, allBooks } from '../data/bookChapters';

export function getBooksIndexData() {
  const versePages = Object.values(verseData).flatMap(book => Object.values(book));
  const books = allBooks;

  const booksWithStats = books.map(book => {
    const bookVerses = versePages.filter(v => v.book === book);
    const chapters = new Set(bookVerses.map(v => v.chapter)).size;
    return { book, bookVerses, chapters };
  });

  return { booksWithStats };
}