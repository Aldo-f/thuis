/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Thuis Documentation',
  tagline: 'Documentation for Thuis VRT MAX Content Monitor',
  favicon: 'img/favicon.svg',
  url: 'https://Aldo-f.github.io',
  baseUrl: '/thuis/',
  organizationName: 'Aldo-f',
  projectName: 'thuis',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      {
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          routeBasePath: '/', // serve docs from root
          editUrl: 'https://github.com/Aldo-f/thuis/edit/main/',
        },
        blog: {
          showReadingTime: true,
          editUrl: 'https://github.com/Aldo-f/thuis/edit/main/blog/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  themeConfig: /** @type {import('@docusaurus/preset-classic').ThemeConfig} */ ({
    navbar: {
      title: 'Thuis Docs',
      logo: {
        alt: 'Thuis Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Tutorial',
        },
        { to: '/blog', label: 'Blog', position: 'left' },
        {
          href: 'https://github.com/Aldo-f/thuis',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Tutorial',
              to: '/intro',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/Aldo-f/thuis',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Aldo-f. Built with Docusaurus.`,
    },
  }),
};

module.exports = config;
