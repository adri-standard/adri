import React from 'react';
import Layout from '@theme-original/Layout';
import type {ReactNode} from 'react';
import VersionFooter from '@site/src/components/VersionFooter';

export default function LayoutWrapper(props: any): ReactNode {
  return (
    <>
      <Layout {...props} />
      <VersionFooter />
    </>
  );
}
