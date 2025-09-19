import React from 'react';
import { useLocation } from '@docusaurus/router';
import type { ReactNode } from 'react';

export default function VersionFooter(): ReactNode {
  const location = useLocation();

  // Determine audience based on current path
  const isContributorSection = location.pathname.includes('/contributors');
  const isUserSection = location.pathname.includes('/users');

  // Get version info (in production this would fetch from package.json/git)
  const packageVersion = "3.0.1"; // Would be dynamic in production
  const gitCommit = "b4e36b4"; // Would be dynamic in production
  const buildDate = new Date().toLocaleDateString();

  if (isContributorSection) {
    return (
      <div style={{
        fontSize: '0.85em',
        color: '#666',
        textAlign: 'center',
        padding: '8px',
        borderTop: '1px solid #eee',
        backgroundColor: '#f8f9fa'
      }}>
        📝 <strong>Contributor Documentation</strong> |
        Updated from commit <code>{gitCommit}</code> |
        Built on {buildDate} |
        Package version: <code>v{packageVersion}</code>
      </div>
    );
  }

  if (isUserSection) {
    return (
      <div style={{
        fontSize: '0.85em',
        color: '#666',
        textAlign: 'center',
        padding: '8px',
        borderTop: '1px solid #eee',
        backgroundColor: '#f8f9fa'
      }}>
        📦 <strong>Package Consumer Documentation</strong> |
        Documentation for ADRI <code>v{packageVersion}</code> |
        Stable release documentation |
        Built on {buildDate}
      </div>
    );
  }

  // Default footer for homepage
  return (
    <div style={{
      fontSize: '0.85em',
      color: '#666',
      textAlign: 'center',
      padding: '8px',
      borderTop: '1px solid #eee',
      backgroundColor: '#f8f9fa'
    }}>
      🏠 <strong>ADRI Documentation</strong> |
      Choose your audience above |
      Version <code>v{packageVersion}</code>
    </div>
  );
}
