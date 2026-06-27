import {type ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

/* ── Inline SVG Icons ────────────────────────────────────────────── */

function DownloadIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="8" y="30" width="24" height="3" rx="1.5" fill="currentColor" />
      <path d="M20 6v18M12 16l8 8 8-8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 20s7-12 16-12 16 12 16 12-7 12-16 12-16-12-16-12z" stroke="currentColor" strokeWidth="2.5" />
      <circle cx="20" cy="20" r="4" fill="currentColor" />
    </svg>
  );
}

function LayersIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="5" width="28" height="9" rx="2" stroke="currentColor" strokeWidth="2.5" />
      <rect x="6" y="15" width="28" height="9" rx="2" stroke="currentColor" strokeWidth="2.5" />
      <rect x="6" y="25" width="28" height="9" rx="2" stroke="currentColor" strokeWidth="2.5" fill="currentColor" fillOpacity="0.15" />
    </svg>
  );
}

function FolderIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 12a2 2 0 012-2h9l3 4h14a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V12z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  );
}

function CogIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="6" stroke="currentColor" strokeWidth="2.5" />
      <path d="M20 2v6M20 32v6M5.86 5.86l4.24 4.24M29.9 29.9l4.24 4.24M2 20h6M32 20h6M5.86 34.14l4.24-4.24M29.9 10.1l4.24-4.24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 4L6 10v8c0 10 6.5 16 14 18 7.5-2 14-8 14-18v-8L20 4z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M16 20l3 3 5-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Feature Data ────────────────────────────────────────────────── */

const features: Array<{
  Icon: () => ReactNode;
  title: string;
  description: string;
}> = [
  {
    Icon: DownloadIcon,
    title: 'Download VRT MAX Videos',
    description:
      'Download your favorite shows from VRT MAX with a single command. No complex configuration needed.',
  },
  {
    Icon: EyeIcon,
    title: 'Dry-Run Mode',
    description:
      'Preview what would be downloaded before committing. See filenames and formats without fetching anything.',
  },
  {
    Icon: LayersIcon,
    title: 'Batch Processing',
    description:
      'Pass multiple URLs at once or use a file with one URL per line. Download entire series in one go.',
  },
  {
    Icon: FolderIcon,
    title: 'Custom Output Directory',
    description:
      'Choose where your videos are saved with the -S or --output-dir flag.',
  },
  {
    Icon: CogIcon,
    title: 'YT-DLP Powered',
    description:
      'Built on top of yt-dlp, the industry-standard video downloader, with a custom patch for VRT MAX support.',
  },
  {
    Icon: ShieldIcon,
    title: 'Built-in Credentials',
    description:
      'Works out of the box with demo credentials. Use your own VRT MAX account via environment variables.',
  },
];

/* ── Terminal Demo ───────────────────────────────────────────────── */

function TerminalDemo() {
  return (
    <div className={styles.terminal}>
      <div className={styles.terminalBar}>
        <div className={styles.terminalDots}>
          <span className={clsx(styles.terminalDot, styles.dotRed)} />
          <span className={clsx(styles.terminalDot, styles.dotYellow)} />
          <span className={clsx(styles.terminalDot, styles.dotGreen)} />
        </div>
        <span className={styles.terminalLabel}>bash — thuis</span>
      </div>
      <div className={styles.terminalContent}>
        <div className={styles.terminalLine}>
          <span className={styles.prompt}>$</span> thuis.sh{' '}
          <span className={styles.url}>https://vrt.be/vrtmax/a/show/journaal</span>
        </div>
        <div className={styles.terminalLine}>
          <span className={styles.success}>&#10003;</span> Logged in as demo user
        </div>
        <div className={styles.terminalLine}>
          <span className={styles.success}>&#10003;</span> Downloading: &ldquo;Het Journaal&rdquo;{' '}
          <span className={styles.dim}>[1080p]</span>
        </div>
        <div className={styles.terminalLine}>
          <span className={styles.success}>&#10003;</span> Complete —{' '}
          <span className={styles.dim}>2.4 GB saved</span>
        </div>
      </div>
    </div>
  );
}

/* ── Hero ────────────────────────────────────────────────────────── */

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={styles.heroBanner}>
      <div className={styles.heroOverlay} />
      <div className={clsx('container', styles.heroContainer)}>
        <div className={styles.heroContent}>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <div className={styles.heroButtons}>
            <Link
              className={clsx('button button--primary button--lg', styles.heroBtnPrimary)}
              to="/docs/intro">
              Get Started
            </Link>
            <Link
              className={clsx('button button--secondary button--lg', styles.heroBtnSecondary)}
              to="https://github.com/Aldo-f/thuis">
              View on GitHub
            </Link>
          </div>
          <TerminalDemo />
        </div>
      </div>
    </header>
  );
}

/* ── Feature Card ────────────────────────────────────────────────── */

function FeatureCard({
  Icon,
  title,
  description,
  index,
}: {
  Icon: () => ReactNode;
  title: string;
  description: string;
  index: number;
}) {
  return (
    <div
      className={styles.cardWrapper}
      style={{animationDelay: `${index * 0.1}s`}}>
      <div className={styles.card}>
        <div className={styles.cardIcon}>
          <Icon />
        </div>
        <Heading as="h3" className={styles.cardTitle}>
          {title}
        </Heading>
        <p className={styles.cardDesc}>{description}</p>
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────── */

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description="Download videos from VRT MAX with thuis, a proof-of-concept downloader powered by yt-dlp.">
      <HomepageHeader />
      <main>
        <section className={styles.featuresSection}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <Heading as="h2" className={styles.sectionTitle}>
                Features
              </Heading>
              <p className={styles.sectionSubtitle}>
                Everything you need to download from VRT MAX
              </p>
            </div>
            <div className={styles.cardGrid}>
              {features.map((feature, idx) => (
                <FeatureCard key={feature.title} {...feature} index={idx} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
