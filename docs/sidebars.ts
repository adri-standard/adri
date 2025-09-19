import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // ADRI Documentation organized by audience
  tutorialSidebar: [
    'intro',  // Homepage audience router
    {
      type: 'category',
      label: '🚀 Package Consumers',
      link: {
        type: 'generated-index',
        title: 'Package Consumer Documentation',
        description: 'Learn how to use ADRI in your AI projects',
        slug: '/users',
      },
      items: [
        'users/getting-started',
        'users/faq',
        'users/frameworks',
        'users/API_REFERENCE',
        'users/WHY_OPEN_SOURCE',
      ],
    },
    {
      type: 'category',
      label: '🛠️ Contributors',
      link: {
        type: 'generated-index',
        title: 'Contributor Documentation',
        description: 'Help improve ADRI - development guides and technical details',
        slug: '/contributors',
      },
      items: [
        'contributors/development-workflow',
        'contributors/framework-extension-pattern',
      ],
    },
  ],
};

export default sidebars;
