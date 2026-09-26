import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://ashworx-global.github.io',
  base: '/vault',
  output: 'static',
  integrations: [mdx(), tailwind()],
  markdown: {
    remarkPlugins: ['remark-gfm'],
    rehypePlugins: ['rehype-slug', 'rehype-autolink-headings'],
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
  },
  vite: {
    resolve: {
      alias: {
        '@': '/src',
      },
    },
  },
});