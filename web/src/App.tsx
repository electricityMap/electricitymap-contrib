import { App as Cap } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { ToastProvider } from '@radix-ui/react-toast';
import * as Sentry from '@sentry/react';
import useGetState from 'api/getState';
import LoadingOverlay from 'components/LoadingOverlay';
import { OnboardingModal } from 'components/modals/OnboardingModal';
import ErrorComponent from 'features/error-boundary/ErrorBoundary';
import Header from 'features/header/Header';
import UpdatePrompt from 'features/service-worker/UpdatePrompt';
import { useDarkMode } from 'hooks/theme';
import { lazy, ReactElement, Suspense, useEffect, useLayoutEffect } from 'react';
import trackEvent from 'utils/analytics';
import { useIsMobile } from 'utils/styling';

const MapWrapper = lazy(async () => import('features/map/MapWrapper'));
const LeftPanel = lazy(async () => import('features/panels/LeftPanel'));
const MapOverlays = lazy(() => import('components/MapOverlays'));
const FAQModal = lazy(() => import('features/modals/FAQModal'));
const InfoModal = lazy(() => import('features/modals/InfoModal'));
const SettingsModal = lazy(() => import('features/modals/SettingsModal'));
const TimeControllerWrapper = lazy(() => import('features/time/TimeControllerWrapper'));
const AnnouncementModal = lazy(() => import('features/modals/AnnouncementModal'));

const isProduction = import.meta.env.PROD;

if (isProduction) {
  trackEvent('App Loaded', {
    isNative: Capacitor.isNativePlatform(),
    platform: Capacitor.getPlatform(),
  });
}

function LeftElementsWrapper(): ReactElement {
  const isMobile = useIsMobile();

  return isMobile ? (
    <div className="absolute bottom-0 left-0 top-0 z-50 h-full w-full">
      <Suspense>
        <LeftPanel />
      </Suspense>
      <Suspense>
        <TimeControllerWrapper />
      </Suspense>
    </div>
  ) : (
    <div className="pointer-events-none absolute left-0 top-0 z-50 my-2 ml-2 flex h-full max-h-[calc(100%-5rem)] w-[500px] flex-col justify-end gap-2 overflow-x-visible">
      <Suspense>
        <LeftPanel />
      </Suspense>
      <Suspense>
        <TimeControllerWrapper />
      </Suspense>
    </div>
  );
}

export default function App(): ReactElement {
  // Triggering the useGetState hook here ensures that the app starts loading data as soon as possible
  // instead of waiting for the map to be lazy loaded.
  // TODO: Replace this with prefetching once we have latest endpoints available for all state aggregates
  useGetState();
  const shouldUseDarkMode = useDarkMode();

  // Update classes on theme change
  useLayoutEffect(() => {
    document.documentElement.classList.toggle('dark', shouldUseDarkMode);
  }, [shouldUseDarkMode]);

  // Handle back button on Android
  useEffect(() => {
    if (Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android') {
      Cap.addListener('backButton', () => {
        if (window.location.pathname === '/map') {
          Cap.exitApp();
        } else {
          window.history.back();
        }
      });
    }
  }, []);

  return (
    <Suspense fallback={<div />}>
      <main className="fixed flex h-screen w-screen flex-col">
        <ToastProvider duration={20_000}>
          <Suspense>
            <Header />
          </Suspense>
          <div className="relative flex flex-auto items-stretch">
            <Sentry.ErrorBoundary fallback={ErrorComponent} showDialog>
              <Suspense>
                <UpdatePrompt />
              </Suspense>
              <Suspense>
                <LoadingOverlay />
              </Suspense>
              <Suspense>
                <OnboardingModal />
                <AnnouncementModal />
              </Suspense>
              <Suspense>
                <FAQModal />
                <InfoModal />
                <SettingsModal />
              </Suspense>
              <LeftElementsWrapper />
              <Suspense>
                <MapWrapper />
              </Suspense>
              <Suspense>
                <MapOverlays />
              </Suspense>
            </Sentry.ErrorBoundary>
          </div>
        </ToastProvider>
      </main>
    </Suspense>
  );
}
