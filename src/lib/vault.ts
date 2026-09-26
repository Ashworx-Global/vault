import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { glob } from 'glob';

const VAULT_ROOT = process.cwd();

export interface Frontmatter {
  tags?: string[];
  aliases?: string[];
  cssclasses?: string[];
  [key: string]: unknown;
}

export interface ProcessedPage {
  slug: string;
  title: string;
  content: string;
  frontmatter: Frontmatter;
  type: 'daily' | 'verse' | 'other';
  book?: string;
  chapter?: string;
  verse?: string;
  date?: string;
  sourceFile: string;
}

export interface DailyNote extends ProcessedPage {
  type: 'daily';
  date: string;
  passages: string[];
  versePages: string[];
}

export interface VersePage extends ProcessedPage {
  type: 'verse';
  book: string;
  chapter: string;
  verse: string;
  reference: string;
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

function parseWikilinks(content: string): string {
  // Convert [[wikilink]] to <a class="wikilink" href="...">wikilink</a>
  // Handle [[link|alias]] format
  return content.replace(/\[\[([^\]]+)\]\]/g, (match, linkContent) => {
    const [link, alias] = linkContent.split('|');
    const displayText = alias || link;
    const cleanLink = link.trim();
    
    // Determine the URL based on link type
    let href = '';
    if (cleanLink.includes(' v ') || cleanLink.match(/\d+ v \d+/)) {
      // Verse page: "Zechariah 8 v 1–23"
      const parts = cleanLink.split(' v ');
      const book = parts[0].trim();
      const verseRef = parts[1].trim().replace(/–/g, '-');
      href = `/bible/${slugify(book)}/${slugify(verseRef)}`;
    } else if (cleanLink.match(/^\d{4}-\d{2}-\d{2}/)) {
      // Daily note with date prefix
      href = `/daily/${slugify(cleanLink)}`;
    } else if (cleanLink.includes(' ')) {
      // Could be a book chapter like "Zechariah 8" or "Acts 23"
      const parts = cleanLink.split(' ');
      const book = parts[0];
      const chapter = parts[1];
      if (/^\d+$/.test(chapter)) {
        href = `/bible/${slugify(book)}/${slugify(chapter)}`;
      } else {
        href = `/search?q=${encodeURIComponent(cleanLink)}`;
      }
    } else {
      // Book name or other
      href = `/bible/${slugify(cleanLink)}`;
    }
    
    return `<a class="wikilink" href="${href}" data-wikilink="${cleanLink}">${displayText}</a>`;
  });
}

function parseLogosLinks(content: string): string {
  // Preserve Logos/ref.ly links as-is - they should open in Logos app
  // These are already in markdown format [text](https://ref.ly/...)
  // We just need to ensure they have target="_blank" and rel="noopener"
  return content.replace(
    /\[([^\]]+)\]\((https?:\/\/ref\.ly\/[^)]+)\)/g,
    '<a class="wikilink-external" href="$2" target="_blank" rel="noopener noreferrer" data-logos-link>$1</a>'
  );
}

function parseBibleCallouts(content: string): string {
  // Convert > [!bible]- [Title](url) blocks to styled details/summary
  const calloutRegex = /> \[!bible\]-\s*\[([^\]]+)\]\(([^)]+)\)\n((?:>.*\n?)*)/g;
  
  return content.replace(calloutRegex, (match, title, url, verses) => {
    const verseLines = verses
      .split('\n')
      .filter(line => line.startsWith('>'))
      .map(line => line.replace(/^>\s*/, ''))
      .join('\n');
    
    return `<details class="bible-callout">
<summary>${title}</summary>
<div class="verse-content">${parseWikilinks(parseLogosLinks(verseLines))}</div>
<p><a href="${url}" target="_blank" rel="noopener noreferrer" class="wikilink-external">Open in Bible Gateway ↗</a></p>
</details>`;
  });
}

function processMarkdown(content: string): string {
  // Process in order: callouts first, then wikilinks, then logos links
  let processed = parseBibleCallouts(content);
  processed = parseWikilinks(processed);
  processed = parseLogosLinks(processed);
  return processed;
}

export async function loadAllPages(): Promise<ProcessedPage[]> {
  const pages: ProcessedPage[] = [];
  
  // Load daily notes
  const dailyFiles = await glob('Daily/*.md', { cwd: VAULT_ROOT });
  for (const file of dailyFiles) {
    const fullPath = path.join(VAULT_ROOT, file);
    const content = fs.readFileSync(fullPath, 'utf-8');
    const { data: frontmatter, content: markdownContent } = matter(content);
    
    // Extract date from filename
    const dateMatch = file.match(/(\d{4}-\d{2}-\d{2})/);
    const date = dateMatch ? dateMatch[1] : '';
    
    // Extract verse page links from harvested section
    const versePageMatches = [...markdownContent.matchAll(/\[\[([^\]]+ v [^\]]+)\]\]/g)];
    const versePages = versePageMatches.map(m => m[1]);
    
    // Extract passage references from top of file
    const passageMatches = [...markdownContent.matchAll(/\[([A-Za-z0-9\s]+\d+:\d+(?:[–-]\d+)?)\]\(https?:\/\/ref\.ly\/[^)]+\)/g)];
    const passages = passageMatches.map(m => m[1]);
    
    const title = file.replace('.md', '').replace(/^\d{4}-\d{2}-\d{2}\s*\(?/, '').replace(/\)?$/, '');
    
    pages.push({
      slug: `daily/${slugify(file.replace('.md', ''))}`,
      title,
      content: processMarkdown(markdownContent),
      frontmatter,
      type: 'daily',
      date,
      passages,
      versePages,
      sourceFile: file,
    });
  }
  
  // Load verse pages
  const verseFiles = await glob('Bible/**/*.md', { cwd: VAULT_ROOT });
  for (const file of verseFiles) {
    const fullPath = path.join(VAULT_ROOT, file);
    const content = fs.readFileSync(fullPath, 'utf-8');
    const { data: frontmatter, content: markdownContent } = matter(content);
    
    // Parse book/chapter/verse from filename
    const fileName = path.basename(file, '.md');
    const parts = fileName.split(' v ');
    const book = parts[0];
    const verse = parts[1] || '';
    const chapter = verse.split(' ')[0] || '';
    
    // Create clean reference
    const reference = `${book} ${verse}`.trim();
    
    pages.push({
      slug: `bible/${slugify(book)}/${slugify(verse)}`,
      title: reference,
      content: processMarkdown(markdownContent),
      frontmatter,
      type: 'verse',
      book,
      chapter,
      verse,
      reference,
      sourceFile: file,
    });
  }
  
  return pages;
}

export async function getDailyNotes(): Promise<DailyNote[]> {
  const pages = await loadAllPages();
  return pages.filter(p => p.type === 'daily') as DailyNote[];
}

export async function getVersePages(): Promise<VersePage[]> {
  const pages = await loadAllPages();
  return pages.filter(p => p.type === 'verse') as VersePage[];
}

export async function getPageBySlug(slug: string): Promise<ProcessedPage | null> {
  const pages = await loadAllPages();
  return pages.find(p => p.slug === slug) || null;
}

export async function getRelatedVerses(book: string, chapter?: string): Promise<VersePage[]> {
  const verses = await getVersePages();
  return verses.filter(v => 
    v.book.toLowerCase() === book.toLowerCase() && 
    (!chapter || v.chapter === chapter)
  );
}

export function getAllTags(pages: ProcessedPage[]): string[] {
  const tags = new Set<string>();
  for (const page of pages) {
    if (page.frontmatter.tags) {
      for (const tag of page.frontmatter.tags) {
        tags.add(tag);
      }
    }
  }
  return Array.from(tags).sort();
}

export function getBooks(verses: VersePage[]): string[] {
  const books = new Set<string>();
  for (const verse of verses) {
    books.add(verse.book);
  }
  return Array.from(books).sort();
}