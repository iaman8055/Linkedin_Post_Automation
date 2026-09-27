import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { QualityCheckPanel } from './QualityCheckPanel'

describe('QualityCheckPanel', () => {
  it('shows structured issues without offering automatic rewriting', () => {
    render(<QualityCheckPanel result={{
      post_id: 'post-1', status: 'warning', ai_review_performed: true, job_id: 'job-1',
      issues: [{ type: 'unsupported_claim', severity: 'medium', message: 'A claim needs support.', suggestion: 'Add a source.' }],
    }}/>)
    expect(screen.getByText('unsupported claim')).toBeInTheDocument()
    expect(screen.getByText('A claim needs support.')).toBeInTheDocument()
    expect(screen.getByText(/does not modify/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /rewrite/i })).not.toBeInTheDocument()
  })
})
