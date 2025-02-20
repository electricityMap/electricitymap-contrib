import { ONE_HOUR, ONE_MINUTE } from 'api/helpers';
import { Toast, useToastReference } from 'components/Toast';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useRegisterSW } from 'virtual:pwa-register/react';

function UpdatePrompt() {
  const reference = useToastReference();
  const { t } = useTranslation();
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW: (_swURL, registration) => {
      if (!registration) {
        console.warn('Service Worker registration is null');
        return;
      }

      setInterval(
        () => {
          console.info(`Checking for app update...`);
          registration.update().catch((error) => {
            console.error('Failed to update Service Worker:', error);
          });
        },
        import.meta.env.PROD ? ONE_HOUR : 10 * 1000
      );
    },
    onRegisterError(error) {
      console.error('SW registration failed:', error);
    },
  });

  const close = () => setNeedRefresh(false);

  const update = () => updateServiceWorker(true);

  useEffect(() => {
    if (needRefresh) {
      reference.current?.publish();
    }
  }, [needRefresh, reference]);

  return (
    <Toast
      ref={reference}
      description={t('updatePrompt.description')}
      toastAction={update}
      isCloseable={true}
      toastActionText={t('updatePrompt.update')}
      toastClose={close}
      toastCloseText={t('updatePrompt.dismiss')}
      duration={ONE_MINUTE}
    />
  );
}

export default UpdatePrompt;
