import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'ADRI Documentation',
  tagline: 'Stop AI agents from breaking on bad data',
  favicon: 'img/adri-favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://adri-standard.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/adri/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'adri-standard', // Usually your GitHub org/user name.
  projectName: 'adri', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // Enable Mermaid diagrams in Markdown
  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/adri-standard/adri/edit/main/docs/',
        },
        blog: false, // Disable blog for documentation site
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'ADRI',
      logo: {
        alt: 'ADRI Logo',
        src: 'img/adri-logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentation',
        },
        { to: '/docs/users/getting-started', label: 'Getting Started', position: 'left' },
        { to: '/docs/users/core-concepts', label: 'Core Concepts', position: 'left' },
        { to: '/docs/users/API_REFERENCE', label: 'API Reference', position: 'left' },
        {
          href: 'https://github.com/adri-standard/adri',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '🚀 Package Consumers',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/users/getting-started',
            },
            {
              label: 'Core Concepts',
              to: '/docs/users/core-concepts',
            },
            {
              label: 'API Reference',
              to: '/docs/users/API_REFERENCE',
            },
            {
              label: 'FAQ',
              to: '/docs/users/faq',
            },
          ],
        },
        {
          title: '🛠️ Contributors',
          items: [
            {
              label: 'Development Workflow',
              to: '/docs/contributors/development-workflow',
            },
            {
              label: 'Framework Extensions',
              to: '/docs/contributors/framework-extension-pattern',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/adri-standard/adri',
            },
            {
              label: 'Issues',
              href: 'https://github.com/adri-standard/adri/issues',
            },
            {
              label: 'Why Open Source',
              to: '/docs/users/WHY_OPEN_SOURCE',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} ADRI Standard Contributors. ADRI™ is founded and maintained by <a href="https://verodat.com">Verodat</a>. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
