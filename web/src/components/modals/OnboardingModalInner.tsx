import { Button } from 'components/Button';
import { TFunction } from 'i18next';
import { Check, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { ReactElement, useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

export interface Page {
  headerImage: { pathname: string };
  isMainTitle?: boolean;
  renderContent: (translator: TFunction) => ReactElement;
  hasWebp?: boolean;
}

function Modal({
  modalName,
  views,
  visible,
  onDismiss,
}: {
  modalName: string;
  views: Page[];
  visible: boolean;
  onDismiss: () => void;
}) {
  const { t } = useTranslation();
  const [currentViewIndex, setCurrentViewIndex] = useState(0);
  const isOnLastView = useCallback(
    () => currentViewIndex === views.length - 1,
    [currentViewIndex, views.length]
  );
  const isOnFirstView = useCallback(() => currentViewIndex === 0, [currentViewIndex]);

  const handleBack = useCallback(() => {
    if (!isOnFirstView()) {
      setCurrentViewIndex(currentViewIndex - 1);
    }
  }, [currentViewIndex, isOnFirstView]);

  const handleForward = useCallback(() => {
    if (!isOnLastView()) {
      setCurrentViewIndex(currentViewIndex + 1);
    }
  }, [currentViewIndex, isOnLastView]);

  if (!visible) {
    return null;
  }
  const currentView = views[currentViewIndex];

  const RightButton = isOnLastView() ? (
    <Button icon={<Check />} onClick={onDismiss} dataTestId="close-modal" />
  ) : (
    <Button icon={<ChevronRight />} onClick={handleForward} type="secondary" />
  );

  return (
    <>
      <div
        className="absolute inset-0 z-50 bg-gray-800/20"
        onClick={onDismiss}
        onKeyDown={onDismiss}
        role="presentation"
      />
      <div
        className="px-auto fixed top-1/2 z-50 w-full -translate-y-1/2 sm:min-w-[500px]"
        data-testid={modalName}
      >
        <div className="flex items-center justify-center self-center">
          <div className="z-10 -mr-4 flex w-full max-w-[35px] flex-col items-start pl-1 sm:mr-0 sm:max-w-[60px] sm:items-end sm:px-2">
            {!isOnFirstView() && (
              <Button
                icon={<ChevronLeft />}
                onClick={handleBack}
                type="secondary"
                dataTestId="back-button"
              />
            )}
          </div>
          <div className="relative flex h-[450px] w-auto max-w-[500px] flex-col rounded-3xl bg-gray-50 shadow-lg dark:bg-gray-700 sm:h-[500px]">
            <Button
              icon={<X />}
              backgroundClasses="absolute self-end m-4"
              onClick={onDismiss}
              type="secondary"
              dataTestId="close-modal"
            />
            <div
              className={`flex h-1/2 max-h-[264px] w-full grow self-center
                rounded-t-3xl bg-auto bg-center bg-no-repeat ${
                  isOnFirstView() ? 'max-w-[10rem] dark:invert' : ''
                }`}
              style={
                currentView.headerImage && !currentView.hasWebp
                  ? {
                      backgroundImage: `url("${currentView.headerImage.pathname}")`,
                      backgroundSize: `${currentView.isMainTitle ? 'contain' : 'cover'} `,
                    }
                  : {}
              }
            >
              {currentView.headerImage && currentView.hasWebp && (
                <picture className="overflow-hidden" style={{}}>
                  <source
                    srcSet={`${currentView.headerImage.pathname}.webp`}
                    type="image/webp"
                  />
                  <img
                    src={`${currentView.headerImage.pathname}.png`}
                    alt=""
                    className="w-full rounded-t-3xl object-top"
                    draggable={false}
                  />
                </picture>
              )}
            </div>
            <div className="flex w-auto flex-col justify-center overflow-y-scroll rounded-b-3xl px-4 pt-6 text-center dark:bg-gray-700">
              {currentView.renderContent(t)}
            </div>
          </div>
          <div className="z-10 -ml-4 flex w-full max-w-[35px] flex-col items-end px-2 sm:ml-0 sm:max-w-[60px]">
            {RightButton}
          </div>
        </div>
        <div className="flex h-[40px] justify-center pt-6">
          {views.map((view: Page, index: number) => (
            <button
              key={`modal-step-item-${index}`}
              className={` mx-2 inline-block h-[14px] w-[14px] rounded-xl ${
                index === currentViewIndex ? 'bg-brand-green' : 'bg-white'
              }`}
              onClick={() => setCurrentViewIndex(index)}
            />
          ))}
        </div>
      </div>
    </>
  );
}

export default Modal;
