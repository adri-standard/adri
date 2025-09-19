import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '🛡️ One-Decorator Protection',
    Svg: require('@site/static/img/adri-logo.svg').default,
    description: (
      <>
        Add <code>@adri_protected</code> to any function and ADRI automatically
        validates data quality before your AI agents process it.
      </>
    ),
  },
  {
    title: '🤖 Framework Agnostic',
    Svg: require('@site/static/img/adri-logo.svg').default,
    description: (
      <>
        Works seamlessly with LangChain, CrewAI, AutoGen, LlamaIndex, and any
        Python function. No framework lock-in, universal protection.
      </>
    ),
  },
  {
    title: '📊 5-Dimension Validation',
    Svg: require('@site/static/img/adri-logo.svg').default,
    description: (
      <>
        Comprehensive validation across validity, completeness, freshness,
        consistency, and plausibility with detailed audit logging.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
