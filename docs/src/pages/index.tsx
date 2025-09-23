import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          Stop AI Agents Breaking on Bad Data
        </Heading>
        <p className="hero__subtitle">
          ADRI creates a data quality contract from your good dataset, then blocks dirty inputs with one decorator.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/users/getting-started">
            Get a 5 Minute Win
          </Link>
          <Link
            className="button button--outline button--lg margin-left--md"
            to="/docs/users/adoption-journey">
            Plan the Adoption Journey →
          </Link>
        </div>
      </div>
    </header>
  );
}

function QuickStartPanel(): ReactNode {
  return (
    <section className="margin-vert--lg">
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <h2>Copy/Paste Quickstart</h2>
            <p className="margin-bottom--sm">
              <Link className="button button--sm button--outline" to="https://pypi.org/project/adri/" target="_blank" rel="noopener noreferrer">PyPI</Link>
              <Link className="button button--sm button--outline margin-left--sm" to="https://github.com/adri-standard/adri" target="_blank" rel="noopener noreferrer">GitHub</Link>
            </p>
            <CodeBlock language="bash">
{`pip install adri
adri setup --guide
adri generate-standard examples/data/invoice_data.csv \
  --output examples/standards/invoice_data_ADRI_standard.yaml
adri assess examples/data/test_invoice_data.csv \
  --standard examples/standards/invoice_data_ADRI_standard.yaml`}
            </CodeBlock>
          </div>
          <div className="col col--6">
            <h2>Protect a Function</h2>
            <CodeBlock language="python">
{`from adri import adri_protected

@adri_protected(standard="invoice_data_standard", data_param="invoice_rows")
def your_agent_function(invoice_rows):
    return agent_pipeline(invoice_rows)`}
            </CodeBlock>
            <p className="margin-top--sm">
              See <Link to="/docs/users/core-concepts">Core Concepts</Link> for the five dimensions and protection modes.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function FourStepCapsule(): ReactNode {
  return (
    <section className="margin-vert--md">
      <div className="container">
        <div className="row" style={{justifyContent: 'center', gap: '0.5rem'}}>
          <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-install">1. Install</Link>
          <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-generate">2. Generate</Link>
          <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-assess">3. Assess</Link>
          <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-protect">4. Decorate</Link>
        </div>
      </div>
    </section>
  );
}

function StartBuildingCards(): ReactNode {
  return (
    <section className="margin-vert--lg">
      <div className="container">
        <div className="row">
          <div className="col col--4">
            <div className="card">
              <div className="card__header"><h3>Generate a Standard</h3></div>
              <div className="card__body">
                Create a YAML contract from known-good data for reuse across flows.
              </div>
              <div className="card__footer">
                <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-generate">Open section</Link>
              </div>
            </div>
          </div>
          <div className="col col--4">
            <div className="card">
              <div className="card__header"><h3>Assess a Dataset</h3></div>
              <div className="card__body">
                Score inbound batches before your agent runs. Spot issues fast.
              </div>
              <div className="card__footer">
                <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-assess">Open section</Link>
              </div>
            </div>
          </div>
          <div className="col col--4">
            <div className="card">
              <div className="card__header"><h3>Guard a Function</h3></div>
              <div className="card__body">
                Add <code>@adri_protected</code> and choose raise/warn/continue on failures.
              </div>
              <div className="card__footer">
                <Link className="button button--secondary button--sm" to="/docs/users/getting-started#step-protect">Open section</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ThreeStepCTA(): ReactNode {
  return (
    <section className="margin-vert--lg">
      <div className="container">
        <div className="row">
          <div className="col col--4">
            <h3>1. Generate a Standard</h3>
            <p>
              Run <code>adri setup --guide</code> then
              <br />
              <code>adri generate-standard</code> on a clean dataset to create your YAML contract.
            </p>
          </div>
          <div className="col col--4">
            <h3>2. Validate New Data</h3>
            <p>
              Use <code>adri assess &lt;file&gt; --standard &lt;path&gt;</code> to score every inbound batch before an agent touches it.
            </p>
          </div>
          <div className="col col--4">
            <h3>3. Guard Your Agent</h3>
            <p>
              Wrap your function with <code>@adri_protected(standard=..., data_param=...)</code> and choose whether to raise, warn, or continue on failure.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Stop AI agents from breaking on bad data. ADRI generates data standards and blocks dirty inputs with one decorator.">
      <HomepageHeader />
      <main>
        <QuickStartPanel />
        <FourStepCapsule />
      </main>
    </Layout>
  );
}
