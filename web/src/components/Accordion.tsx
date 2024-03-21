import { title } from 'node:process';

import { useState } from 'react';
import { HiChevronDown, HiChevronUp } from 'react-icons/hi2';

export default function Accordion({
  isCollapsedDefault = true,
  onClick,
  badge,
  className,
  icon,
  children,
  title,
}: {
  isCollapsedDefault?: boolean;
  onClick?: () => void;
  badge?: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  title: string;
}) {
  const [isCollapsed, setIsCollapsed] = useState(isCollapsedDefault);

  const handleToggleCollapse = () => {
    if (onClick != undefined) {
      onClick;
    }
    setIsCollapsed((previous) => !previous);
  };

  return (
    <div className="flex flex-col">
      <button data-test-id="collapse-button" onClick={handleToggleCollapse}>
        <div className={`flex flex-row items-center justify-between ${className}`}>
          <div className="flex w-2/3 flex-initial flex-row gap-2">
            <div className={`flex items-center justify-center`}>{icon}</div>
            <h2
              className={`self-center text-left text-sm font-semibold`}
              data-test-id="title"
            >
              {title}
            </h2>
          </div>
          <div className="flex h-fit flex-row gap-2 text-nowrap">
            {badge}
            <div className="text-lg text-white">
              {isCollapsed ? (
                <div data-test-id="collapse-down">
                  <HiChevronDown />
                </div>
              ) : (
                <div data-test-id="collapse-up">
                  <HiChevronUp />
                </div>
              )}
            </div>
          </div>
        </div>
      </button>
      {!isCollapsed && children}
    </div>
  );
}
