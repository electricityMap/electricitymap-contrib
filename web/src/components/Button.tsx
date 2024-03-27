import React from 'react';
import { twMerge } from 'tailwind-merge';

interface ButtonProps {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  disabled?: boolean;
  size?: 'sm' | 'lg' | 'xl';
  type?: 'primary' | 'secondary' | 'tertiary' | 'link';
  href?: string;
  backgroundClasses?: string;
  foregroundClasses?: string;
  onClick?: () => void;
}

export function Button({
  icon,
  children,
  disabled,
  href,
  backgroundClasses, // backgroundColor, borderColor, margin, etc.
  foregroundClasses, // textColor, etc.
  size = 'lg',
  type = 'primary',
  onClick,
}: ButtonProps) {
  const renderAsLink = Boolean(href);
  const As = renderAsLink ? 'a' : 'button';
  const componentType = renderAsLink ? undefined : 'button';
  const isIconOnly = !children && Boolean(icon);

  return (
    <div
      className={twMerge(
        `items-center justify-center rounded-full ${getBackground(type, disabled)}`,
        backgroundClasses
      )}
    >
      <As
        className={twMerge(
          `flex h-full w-full flex-row items-center justify-center rounded-full text-sm font-semibold
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-green disabled:text-neutral-400
        disabled:hover:bg-inherit disabled:dark:text-gray-500 ${getSize(
          size,
          type,
          isIconOnly
        )}
        ${getForeground(type)} ${getHover(type)}`,
          foregroundClasses
        )}
        disabled={disabled}
        href={href}
        type={componentType}
        onClick={onClick}
        target="_blank"
      >
        {icon}
        {children}
      </As>
    </div>
  );
}

function getHover(type: string) {
  switch (type) {
    case 'primary': {
      return 'hover:bg-black/20';
    }
    default: {
      return 'hover:bg-neutral-400/10';
    }
  }
}

function getBackground(type: string, disabled: boolean | undefined) {
  switch (type) {
    case 'primary': {
      if (disabled) {
        return 'bg-zinc-50 dark:bg-gray-800 border border-neutral-200 dark:border-gray-700';
      }
      return 'bg-brand-green';
    }
    case 'secondary': {
      return 'border dark:border-gray-700 border-neutral-200 bg-white dark:bg-gray-900';
    }
    default: {
      return 'bg-inherit';
    }
  }
}

function getForeground(type: string) {
  switch (type) {
    case 'primary': {
      return 'text-white';
    }
    case 'link': {
      return 'text-emerald-800 dark:text-emerald-500';
    }
    default: {
      return 'text-black dark:text-white';
    }
  }
}

function getSize(size: string, type: string, isIconOnly: boolean) {
  if (isIconOnly) {
    switch (size) {
      case 'sm': {
        return 'min-w-7 min-h-7';
      }
      case 'lg': {
        return 'min-w-11 min-h-11';
      }
      case 'xl': {
        return 'min-w-14 min-h-14';
      }
    }
  }

  switch (size) {
    case 'sm': {
      return 'min-w-6 min-h-6 px-2 py-1 gap-x-1 text-sm';
    }
    case 'lg': {
      return type == 'link'
        ? 'px-4 py-2 gap-x-2 text-sm'
        : 'min-w-10 min-h-10 px-6 py-3 gap-x-1.5 text-sm';
    }
    case 'xl': {
      return type == 'link'
        ? 'px-4 py-2 gap-x-2 text-base'
        : 'min-w-12 min-h-12 px-8 py-4 gap-x-1.5 text-base';
    }
    default: {
      return '';
    }
  }
}
