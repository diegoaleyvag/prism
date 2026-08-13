import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import SimBanner from './SimBanner.svelte';

describe('SimBanner', () => {
	it('renders the SIMULATED disclaimer text', () => {
		render(SimBanner);
		expect(screen.getByText(/SIMULATED/)).toBeInTheDocument();
		expect(screen.getByText(/not named-model performance/i)).toBeInTheDocument();
	});

	it('has no dismiss/close control', () => {
		render(SimBanner);
		expect(screen.queryByRole('button')).not.toBeInTheDocument();
	});
});
