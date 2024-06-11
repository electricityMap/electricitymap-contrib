import * as ToastPrimitive from '@radix-ui/react-toast';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaXmark } from 'react-icons/fa6';

import { Button } from './Button';

type Props = {
  title: string;
  description?: string;
  isCloseable?: boolean;
  toastAction?: () => void;
  toastClose?: () => void;
  toastActionText?: string;
};

function Toast({ title, description, toastAction, toastActionText, toastClose }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  const handleToastAction = () => {
    toastAction?.();
    setOpen(false);
  };
  const handleToastClose = () => {
    toastClose?.();
    setOpen(false);
  };

  return (
    <>
      <ToastPrimitive.Root
        open={open}
        onOpenChange={setOpen}
        duration={60 * 1000}
        type="background"
        className="bg-gray/80 fixed top-16 z-50 m-2 inline-block max-w-max self-center rounded-lg shadow backdrop-blur-sm xs:left-1/2 xs:w-max xs:-translate-x-1/2 xs:transform dark:bg-gray-800/80"
      >
        <div className="flex items-center p-2">
          <div className="flex flex-col">
            <ToastPrimitive.Title className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {title}
            </ToastPrimitive.Title>
            <ToastPrimitive.Description className="mt-1 text-sm text-gray-700 dark:text-gray-400">
              {description}
            </ToastPrimitive.Description>
          </div>
          {toastAction && (
            <ToastPrimitive.Action
              altText="view now"
              className="m-2 flex items-center justify-center "
              onClick={handleToastAction}
            >
              <Button size="md">{toastActionText}</Button>
            </ToastPrimitive.Action>
          )}
          <ToastPrimitive.Close
            className="m-2 flex items-center justify-center"
            onClick={handleToastClose}
            aria-label={t('misc.dismiss')}
          >
            <FaXmark className="h-4 w-4" />
          </ToastPrimitive.Close>
        </div>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport />
    </>
  );
}

export default Toast;
