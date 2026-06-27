import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

function FeatureCard({title, description}: {title: string; description: string}): ReactNode {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={siteConfig.title}
      description="Download videos from VRT MAX with thuis, a proof-of-concept downloader powered by yt-dlp.">
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              <FeatureCard
                title="Download VRT MAX Videos"
                description="Download your favorite shows from VRT MAX with a single command. No complex configuration needed."
              />
              <FeatureCard
                title="Dry-Run Mode"
                description="Preview what would be downloaded before committing. See filenames and formats without fetching anything."
              />
              <FeatureCard
                title="Batch Processing"
                description="Pass multiple URLs at once or use a file with one URL per line. Download entire series in one go."
              />
            </div>
            <div className="row" style={{marginTop: '2rem'}}>
              <FeatureCard
                title="Custom Output Directory"
                description="Choose where your videos are saved with the -S or --output-dir flag."
              />
              <FeatureCard
                title="YT-DLP Powered"
                description="Built on top of yt-dlp, the industry-standard video downloader, with a custom patch for VRT MAX support."
              />
              <FeatureCard
                title="Built-in Credentials"
                description="Works out of the box with demo credentials. Use your own VRT MAX account via environment variables."
              />
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
