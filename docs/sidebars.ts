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
        'users/onboarding-guide',
        'users/feature-benefits',
        'users/flip-to-enterprise',
        'users/core-concepts',
        'users/audit-and-logging',
        'users/config-precedence-and-logging',
        'users/faq',
        'users/frameworks',
        'users/adoption-journey',
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
        'contributors/architecture',
      ],
    },
    {
      type: 'category',
      label: '⚖️ Legal',
      link: {
        type: 'generated-index',
        title: 'Legal Information',
        description: 'Licensing and trademark information for ADRI',
        slug: '/legal',
      },
      items: [
        'legal/trademark-policy',
      ],
    },
  ],
};

export default sidebars;
