import { loadingMapAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import { BottomSheet } from 'react-spring-bottom-sheet';
import { hasOnboardingBeenSeenAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import TimeController from './TimeController';
import TimeHeader from './TimeHeader';

function BottomSheetWrappedTimeController() {
  const isLoadingMap = useAtomValue(loadingMapAtom);
  const hasOnboardingBeenSeen = useAtomValue(hasOnboardingBeenSeenAtom);
  const safeAreaBottomString = getComputedStyle(
    document.documentElement
  ).getPropertyValue('--sab');

  const safeAreaBottom = safeAreaBottomString
    ? Number.parseInt(safeAreaBottomString.replace('px', ''))
    : 0;
  const SNAP_POINTS = [60 + safeAreaBottom, 170 + safeAreaBottom];

  // Don't show the time controller until the onboarding has been seen
  // But it still has to be rendered to avoid re-querying data and showing loading
  // indicators again. Therefore we set the snap points to 0 until modal is closed.
  const snapPoints = hasOnboardingBeenSeen && !isLoadingMap ? SNAP_POINTS : [0, 0];

  return (
    <BottomSheet
      scrollLocking={false} // Ensures scrolling is not blocked on IOS
      open={!isLoadingMap}
      snapPoints={() => snapPoints}
      blocking={false}
      header={<TimeHeader />}
    >
      <TimeController className="p-2 min-[370px]:px-4" />
    </BottomSheet>
  );
}

function FloatingTimeController() {
  return (
    <div className="fixed bottom-3 left-3 z-30 w-[calc(14vw_+_16rem)] rounded-xl bg-white px-4 py-3 shadow-xl drop-shadow-2xl dark:bg-gray-800 min-[780px]:w-[calc((14vw_+_16rem)_-_30px)] xl:px-5">
      <TimeController />
    </div>
  );
}

export default function TimeControllerWrapper() {
  const isBiggerThanMobile = useBreakpoint('sm');
  return isBiggerThanMobile ? (
    <FloatingTimeController />
  ) : (
    <BottomSheetWrappedTimeController />
  );
}
