import { bookChapters, allBooks } from '../data/bookChapters';

export function getBookPageData(book) {
  const bookData = bookChapters[book] || { title: book, chapters: [] };
  const bookIndex = allBooks.indexOf(book);
  const prevBook = bookIndex > 0 ? allBooks[bookIndex - 1] : null;
  const nextBook = bookIndex < allBooks.length - 1 ? allBooks[bookIndex + 1] : null;

  const totalPassages = bookData.chapters.reduce((sum, c) => sum + c.verses.length, 0);
  const totalChapters = bookData.chapters.length;

  const navHtml = (prevBook ? '<a href="/books/' + prevBook + '" class="px-4 py-2 bg-stone-100 text-stone-700 rounded-lg text-sm font-medium hover:bg-primary-50 hover:text-primary-700 transition-colors border border-stone-200 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>' + (prevBook.charAt(0).toUpperCase() + prevBook.slice(1)) + '</a>' : '') + (nextBook ? '<a href="/books/' + nextBook + '" class="px-4 py-2 bg-stone-100 text-stone-700 rounded-lg text-sm font-medium hover:bg-primary-50 hover:text-primary-700 transition-colors border border-stone-200 flex items-center gap-2">' + (nextBook.charAt(0).toUpperCase() + nextBook.slice(1)) + '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></a>' : '');

  const chaptersHtml = bookData.chapters.map(chapter => {
    const versesHtml = chapter.verses.map(verse => {
      const verseUrl = verse.toLowerCase().replace(/ /g, "-").replace(/–/g, "-").replace(/:/g, "");
      return '<article class="p-5 hover:bg-stone-50 transition-colors"><div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4"><div class="flex-1"><h3 class="font-semibold text-stone-900 mb-1"><a href="/bible/' + book + '/' + verseUrl + '" class="hover:text-primary-700 transition-colors">' + verse + '</a></h3></div></div></article>';
    }).join("");
    return '<section class="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden"><header class="bg-stone-50 px-6 py-4 border-b border-stone-200"><h2 class="font-semibold text-stone-900">' + bookData.title + ' ' + chapter.chapter + '</h2><p class="text-sm text-stone-600 mt-1">' + chapter.verses.length + ' verse pages in this chapter</p></header><div class="divide-y divide-stone-100">' + versesHtml + '</div></section>';
  }).join("");

  return {
    title: bookData.title,
    description: 'Browse all verse pages from ' + bookData.title,
    totalPassages: bookData.chapters.reduce((sum, c) => sum + c.verses.length, 0),
    totalChapters: bookData.chapters.length,
    navHtml,
    chaptersHtml,
  };
}