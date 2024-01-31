import { act, renderHook } from '@testing-library/react';

import { useMediaQuery } from './styling';

const BELOW_MIN_WIDTH = 599;
const MIN_WITDH = 600;

describe('useMediaQuery', () => {
  it('renders', () => {
    window.resizeTo(BELOW_MIN_WIDTH, 0);
    const { result } = renderHook(() => useMediaQuery(`(min-width: ${MIN_WITDH}px)`));
    expect(result.current).to.be.false;

    act(() => window.resizeTo(MIN_WITDH, 0));

    expect(result.current).to.be.true;
  });
});
